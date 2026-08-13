#simulation.py
"""
Main controller for the simulation. Owns the cars, riders, map, and the
discrete-event engine that processes rider requests, pickups, and dropoffs
in chronological order.
"""

import os
import heapq
from graph import Graph

TRAVEL_SPEED_FACTOR = 0.1   # converts Manhattan distance into travel time


def calculate_travel_time(start_location, end_location):
    """Placeholder navigation: Manhattan distance scaled into a time cost."""
    (x1, y1), (x2, y2) = start_location, end_location
    distance = abs(x1 - x2) + abs(y1 - y2)
    return distance * TRAVEL_SPEED_FACTOR

class Simulation:
    def __init__(self, map_filename):
        self.trip_log=[]
        self.cars = {}
        self.riders = {}
        self.map = Graph()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.map.load_from_file(os.path.join(base_dir, map_filename))

        # --- event engine state (new this milestone) ---
        self.events = []          # min-heap of (time, seq, event_type, data)
        self.current_time = 0
        self._seq = 0             # monotonic tie-breaker so the heap never
                                  # has to compare event types or objects

    def _schedule(self, timestamp, event_type, data):
            """Only place events are built, so every tuple is a valid 4-tuple."""
            heapq.heappush(self.events, (timestamp, self._seq, event_type, data))
            self._seq += 1

    def find_closest_car_brute_force(self, rider_location):
        """Return the nearest AVAILABLE car, or None if none are free."""
        closest_car = None
        min_distance = float("inf")
        for car in self.cars.values():
            if car.status != "available":
                continue
            (cx, cy), (rx, ry) = car.location, rider_location
            distance = abs(cx - rx) + abs(cy - ry)
            if distance < min_distance:
                min_distance = distance
                closest_car = car
        return closest_car

    def handle_rider_request(self, rider):
        rider.request_time=self.current_time
        car = self.find_closest_car_brute_force(rider.start_location)
        if car is None:
            print(f"TIME {self.current_time:.1f}: no car available for RIDER {rider.id}")
            return

        car.assigned_rider = rider
        car.status = "en_route_to_pickup"

        pickup_duration = calculate_travel_time(car.location, rider.start_location)
        self._schedule(self.current_time + pickup_duration, "ARRIVAL", car)

        print(f"TIME {self.current_time:.1f}: CAR {car.id} dispatched to RIDER {rider.id}")

    def handle_arrival(self, car):
        rider = car.assigned_rider

        if car.status == "en_route_to_pickup":
            print(f"TIME {self.current_time:.1f}: CAR {car.id} picked up RIDER {rider.id}")
            car.location = rider.start_location
            car.status = "en_route_to_destination"
            rider.pickup_time=self.current_time
            rider.status = "in_car"

            dropoff_duration = calculate_travel_time(car.location, rider.destination)
            self._schedule(self.current_time + dropoff_duration, "ARRIVAL", car)

        elif car.status == "en_route_to_destination":
            rider=car.assigned_rider
            rider.dropoff_time=self.current_time
            print(f"TIME {self.current_time:.1f}: CAR {car.id} dropped off RIDER {rider.id}")
            self.log_trip_data(rider)
            car.location = rider.destination
            car.status = "available"
            rider.status = "completed"
            car.assigned_rider = None

    def run(self):
        # Seed a REQUEST event for every rider at its request time.
        for rider in self.riders.values():
            self._schedule(rider.request_time, "REQUEST", rider)

        # Main loop: pop in time order, advance the clock, dispatch.
        while self.events:
            timestamp, _seq, event_type, data = heapq.heappop(self.events)
            self.current_time = timestamp

            if event_type == "REQUEST":
                self.handle_rider_request(data)
            elif event_type == "ARRIVAL":
                self.handle_arrival(data)   

    def log_trip_data(self, rider):
        trip_record={
            'rider_id':rider.id,
            'request_time':rider.request_time,
            'pickup_time':rider.pickup_time,
            'dropoff_time':rider.dropoff_time,
            'wait_time':rider.pickup_time-rider.request_time,
            'trip_duration':rider.dropoff_time-rider.pickup_time
        }
        self.trip_log.append(trip_record)
        print(f"TIME {self.current_time:.2f}: Trip for {rider.id} completed and logged.")

    def analyze_results(self):
        """Proces trip_log to calculate and return final KPI's"""

        if not self.trip_log:
            print("No trips completed, no analysis required.")
            return None
        
        #Calculate individual KPI'set
        total_wait_time=sum(trip['wait_time'] for trip in self.trip_log)
        total_trip_duration=sum(trip['trip_duration'] for trip in self.trip_log)

        total_time_on_trips=total_trip_duration #Assumes travel to pickup in cluded in trip duration for utilization
        num_cars=len(self.cars)
        total_potential_time=num_cars*self.current_time if num_cars>0 else 0

        #Assemble results into a dictionary
        results={
            "completed_trips":len(self.trip_log),
            "average_wait_time":total_wait_time/len(self.trip_log),
            "average_trip_duration":total_trip_duration/len(self.trip_log),
            "driver_utilization_percent":(total_time_on_trips/total_potential_time)*100 if total_potential_time>0 else 0
        }

        #Formatted summary here
        print("\n---Simulation Analysis---")
        print(f"Completed Trips: {results['completed_trips']}")
        print(f"Average Rider Wait Time: {results['average_wait_time']:.2f} time units")
        print(f"Average Trip Duration: {results['average_trip_duration']:.2f} time units")
        print(f"Driver Utilization: {results['driver_utilization_percent']:.2f}%")
        print("-------------------------\n")

        return results
                              
                                  
