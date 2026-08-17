# simulation.py
"""
Discrete-event ride-sharing simulation. Owns the map, the fleet, the
availability index, and the event loop that matches riders to cars using a
Quadtree (geographic candidates) followed by Dijkstra (road travel time).
"""

import os
import heapq
import random
import argparse
from itertools import count

from graph import Graph, find_nearest_vertex
from quadtree import Point, Rectangle, Quadtree
from pathfinding import find_shortest_path
from car import Car
from rider import Rider

DEFAULT_CANDIDATE_COUNT = 5
DEFAULT_MEAN_ARRIVAL_TIME = 2.0


class Simulation:
    def __init__(self, map_filename, num_cars=100,
                 candidate_count=DEFAULT_CANDIDATE_COUNT,
                 max_time=1000.0, num_riders=200,
                 mean_arrival_time=DEFAULT_MEAN_ARRIVAL_TIME,
                 random_seed=None):
        self.trip_log = []
        self.cars = {}
        self.riders = {}

        self.map = Graph()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.map.load_map_data(os.path.join(base_dir, map_filename))

        # Quadtree boundary sized to the map extent plus a margin.
        xs = [c[0] for c in self.map.node_coordinates.values()]
        ys = [c[1] for c in self.map.node_coordinates.values()]
        margin = 1.0
        self.min_x, self.max_x = min(xs), max(xs)
        self.min_y, self.max_y = min(ys), max(ys)
        boundary = Rectangle(
            self.min_x - margin,
            self.min_y - margin,
            (self.max_x - self.min_x) + 2 * margin,
            (self.max_y - self.min_y) + 2 * margin,
        )

        # Three availability structures kept in sync by the two methods below.
        self.available_cars = {}
        self.available_car_points = {}
        self.available_car_quadtree = Quadtree(boundary, capacity=4)

        # Event engine state.
        self.events = []
        self.current_time = 0.0
        self.event_sequence = count()

        # Config + metrics.
        self.candidate_count = candidate_count
        self.max_time = max_time
        self.num_riders = num_riders
        self.mean_arrival_time = mean_arrival_time
        self.rng = random.Random(random_seed)

        self.riders_generated = 0
        self.unmatched_count = 0
        self.sim_span = 0.0

        self._rider_counter = count()

        self.initialize_cars(num_cars)

    # ----- scheduling -----
    def _schedule(self, timestamp, event_type, data):
        heapq.heappush(
            self.events,
            (timestamp, next(self.event_sequence), event_type, data),
        )

    # ----- availability layer -----
    def add_available_car(self, car):
        if car.id in self.available_cars or car.id in self.available_car_points:
            raise ValueError(f"Car {car.id} is already marked available.")

        point = Point(car.location[0], car.location[1], data=car)
        if not self.available_car_quadtree.insert(point):
            raise ValueError(
                f"Car {car.id} at {car.location} is outside the quadtree boundary."
            )

        self.available_cars[car.id] = car
        self.available_car_points[car.id] = point
        car.status = "available"

    def remove_available_car(self, car):
        if car.id not in self.available_car_points:
            raise KeyError(f"Car {car.id} is not currently marked available.")

        point = self.available_car_points[car.id]
        if not self.available_car_quadtree.remove(point):
            raise RuntimeError(
                f"Quadtree/point desync: car {car.id}'s point was not found."
            )

        del self.available_car_points[car.id]
        del self.available_cars[car.id]

    # ----- setup -----
    def initialize_cars(self, num_cars):
        for i in range(num_cars):
            loc = (
                self.rng.uniform(self.min_x, self.max_x),
                self.rng.uniform(self.min_y, self.max_y),
            )
            car = Car(f"CAR{i:03d}", loc)
            self.cars[car.id] = car
            self.add_available_car(car)

    def generate_rider_request(self):
        rider_id = f"RIDER{next(self._rider_counter):04d}"
        start = (
            self.rng.uniform(self.min_x, self.max_x),
            self.rng.uniform(self.min_y, self.max_y),
        )
        dest = (
            self.rng.uniform(self.min_x, self.max_x),
            self.rng.uniform(self.min_y, self.max_y),
        )
        rider = Rider(rider_id, start, dest)
        self.riders[rider.id] = rider
        return rider

    def _schedule_next_request(self):
        if self.riders_generated >= self.num_riders:
            return
        interval = self.rng.expovariate(1.0 / self.mean_arrival_time)
        next_time = self.current_time + interval
        if next_time > self.max_time:
            return
        rider = self.generate_rider_request()
        self._schedule(next_time, "RIDER_REQUEST", rider)
        self.riders_generated += 1

    # ----- matching -----
    def _best_candidate(self, rider):
        query_point = Point(rider.start_location[0], rider.start_location[1])
        candidate_points = self.available_car_quadtree.find_k_nearest(
            query_point, k=self.candidate_count
        )
        if not candidate_points:
            return None, None, None

        rider_vertex = find_nearest_vertex(
            rider.start_location, self.map.node_coordinates
        )

        best_car = None
        best_route = None
        best_time = float("inf")
        for point in candidate_points:
            car = point.data
            car_vertex = find_nearest_vertex(
                car.location, self.map.node_coordinates
            )
            route, travel_time = find_shortest_path(
                self.map, car_vertex, rider_vertex
            )
            if route is None:
                continue
            if travel_time < best_time:   # earlier (nearer) candidate wins ties
                best_time = travel_time
                best_route = route
                best_car = car
        return best_car, best_route, best_time

    def handle_rider_request(self, rider):
        if rider.request_time is None:
            rider.request_time = self.current_time

        best_car, best_route, best_time = self._best_candidate(rider)

        if best_car is None:
            rider.status = "unmatched"
            self.unmatched_count += 1
            print(f"TIME {self.current_time:.1f}: no car for {rider.id}")
        else:
            self.remove_available_car(best_car)
            best_car.status = "en_route_to_pickup"
            best_car.assigned_rider = rider
            best_car.route = best_route
            best_car.route_time = best_time
            best_car.busy_start_time = self.current_time
            rider.status = "waiting"
            self._schedule(self.current_time + best_time, "PICKUP_ARRIVAL", best_car)
            print(f"TIME {self.current_time:.1f}: {best_car.id} -> {rider.id}")

        # Always keep the request stream alive, matched or not.
        self._schedule_next_request()

    def handle_pickup_arrival(self, car):
        rider = car.assigned_rider
        if rider is None:
            return

        car.location = rider.start_location
        car.status = "en_route_to_destination"
        rider.status = "in_car"
        rider.pickup_time = self.current_time

        pickup_vertex = find_nearest_vertex(
            rider.start_location, self.map.node_coordinates
        )
        dest_vertex = find_nearest_vertex(
            rider.destination, self.map.node_coordinates
        )
        route, trip_time = find_shortest_path(self.map, pickup_vertex, dest_vertex)

        if route is None:
            # Destination unreachable: recover without scheduling at infinity.
            rider.status = "unsuccessful"
            self.unmatched_count += 1
            car.total_busy_time += self.current_time - car.busy_start_time
            car.assigned_rider = None
            self.add_available_car(car)
            print(f"TIME {self.current_time:.1f}: {rider.id} unreachable; {car.id} freed")
            return

        car.route = route
        car.route_time = trip_time
        self._schedule(self.current_time + trip_time, "DROPOFF_ARRIVAL", car)
        print(f"TIME {self.current_time:.1f}: {car.id} picked up {rider.id}")

    def handle_dropoff_arrival(self, car):
        rider = car.assigned_rider
        if rider is None:
            return

        car.location = rider.destination
        rider.status = "completed"
        rider.dropoff_time = self.current_time
        car.assigned_rider = None

        self.log_trip_data(rider)
        car.total_busy_time += self.current_time - car.busy_start_time
        car.trips_completed += 1

        self.add_available_car(car)
        print(f"TIME {self.current_time:.1f}: {car.id} dropped off {rider.id}")

    # ----- main loop -----
    def run(self):
        # Seed the first request at time 0 if the limits allow at least one.
        if self.riders_generated < self.num_riders:
            rider = self.generate_rider_request()
            self._schedule(0.0, "RIDER_REQUEST", rider)
            self.riders_generated += 1

        while self.events:
            timestamp, _seq, event_type, data = heapq.heappop(self.events)
            self.current_time = timestamp

            if event_type == "RIDER_REQUEST":
                self.handle_rider_request(data)
            elif event_type == "PICKUP_ARRIVAL":
                self.handle_pickup_arrival(data)
            elif event_type == "DROPOFF_ARRIVAL":
                self.handle_dropoff_arrival(data)
            else:
                raise ValueError(f"Unknown event type: {event_type}")

        self.sim_span = self.current_time

    # ----- metrics -----
    def log_trip_data(self, rider):
        self.trip_log.append({
            "rider_id": rider.id,
            "request_time": rider.request_time,
            "pickup_time": rider.pickup_time,
            "dropoff_time": rider.dropoff_time,
            "wait_time": rider.pickup_time - rider.request_time,
            "trip_duration": rider.dropoff_time - rider.pickup_time,
        })

    def analyze_results(self):
        completed = len(self.trip_log)
        num_cars = len(self.cars)

        if completed == 0:
            avg_wait = 0.0
            avg_trip = 0.0
        else:
            avg_wait = sum(t["wait_time"] for t in self.trip_log) / completed
            avg_trip = sum(t["trip_duration"] for t in self.trip_log) / completed

        total_busy = sum(c.total_busy_time for c in self.cars.values())
        span = self.sim_span if self.sim_span > 0 else self.current_time
        denom = num_cars * span
        utilization = (total_busy / denom) * 100 if denom > 0 else 0.0
        trips_per_car = completed / num_cars if num_cars > 0 else 0.0

        results = {
            "total_riders_generated": self.riders_generated,
            "total_completed": completed,
            "total_unmatched": self.unmatched_count,
            "average_wait_time": avg_wait,
            "average_trip_duration": avg_trip,
            "driver_utilization_percent": utilization,
            "trips_per_car": trips_per_car,
        }

        print("\n--- Simulation Analysis ---")
        print(f"Riders generated:       {results['total_riders_generated']}")
        print(f"Trips completed:        {results['total_completed']}")
        print(f"Unmatched/unsuccessful: {results['total_unmatched']}")
        print(f"Avg rider wait time:    {results['average_wait_time']:.2f}")
        print(f"Avg trip duration:      {results['average_trip_duration']:.2f}")
        print(f"Driver utilization:     {results['driver_utilization_percent']:.2f}%")
        print(f"Trips per car:          {results['trips_per_car']:.2f}")
        print("---------------------------\n")
        return results


def main():
    parser = argparse.ArgumentParser(description="Ride-sharing simulator.")
    parser.add_argument("--map-file", default="city_map.csv")
    parser.add_argument("--num-cars", type=int, default=100)
    parser.add_argument("--num-riders", type=int, default=200)
    parser.add_argument("--max-time", type=float, default=1000.0)
    parser.add_argument("--candidate-count", type=int, default=DEFAULT_CANDIDATE_COUNT)
    parser.add_argument("--mean-arrival", type=float, default=DEFAULT_MEAN_ARRIVAL_TIME)
    parser.add_argument("--random-seed", type=int, default=None)
    parser.add_argument("--output", default="simulation_summary.png")
    parser.add_argument("--no-plot", action="store_true",
                        help="Skip the PNG visualization (metrics only).")
    args = parser.parse_args()

    sim = Simulation(
        map_filename=args.map_file,
        num_cars=args.num_cars,
        candidate_count=args.candidate_count,
        max_time=args.max_time,
        num_riders=args.num_riders,
        mean_arrival_time=args.mean_arrival,
        random_seed=args.random_seed,
    )
    sim.run()
    results = sim.analyze_results()

    if not args.no_plot:
        # Imported here so headless/metrics-only runs don't require matplotlib.
        from visualization import create_summary
        path = create_summary(sim, results, args.output)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
