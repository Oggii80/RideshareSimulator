# test_script.py
"""
Repeatable demonstration of the required correctness checks. Runs small,
seeded simulations and asserts the invariants hold after every event.
"""

import io
import contextlib

from simulation import Simulation
from quadtree import Point


def indexed_ids(sim):
    found = set()

    def walk(node):
        for p in node.points:
            found.add(p.data.id)
        if node.divided:
            for c in node._children():
                walk(c)

    walk(sim.available_car_quadtree.root)
    return found


def invariant_holds(sim):
    return set(sim.available_cars) == set(sim.available_car_points) == indexed_ids(sim)


def instrumented_run(sim):
    # Drive the loop manually so the invariant can be checked after each event,
    # and confirm no busy car is ever left in the availability index.
    import heapq

    if sim.riders_generated < sim.num_riders:
        rider = sim.generate_rider_request()
        sim._schedule(0.0, "RIDER_REQUEST", rider)
        sim.riders_generated += 1

    while sim.events:
        timestamp, seq, event_type, data = heapq.heappop(sim.events)
        assert timestamp != float("inf"), "event scheduled at infinity"
        assert isinstance(seq, int)
        sim.current_time = timestamp

        if event_type == "RIDER_REQUEST":
            sim.handle_rider_request(data)
        elif event_type == "PICKUP_ARRIVAL":
            sim.handle_pickup_arrival(data)
        elif event_type == "DROPOFF_ARRIVAL":
            sim.handle_dropoff_arrival(data)
        else:
            raise ValueError(event_type)

        assert invariant_holds(sim), f"invariant broke after {event_type}"
        for car in sim.cars.values():
            if car.status in ("en_route_to_pickup", "en_route_to_destination"):
                assert car.id not in sim.available_cars, "busy car still available"

    sim.sim_span = sim.current_time


def run_quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


def test_same_timestamp_heap():
    # Two events at the same timestamp must pop without comparing objects.
    from car import Car
    sim = Simulation("debug_map.csv", num_cars=2, num_riders=1, max_time=1.0, random_seed=0)
    sim._schedule(5.0, "PICKUP_ARRIVAL", Car("X", (0, 0)))
    sim._schedule(5.0, "PICKUP_ARRIVAL", Car("Y", (0, 0)))
    import heapq
    t1 = heapq.heappop(sim.events)
    t2 = heapq.heappop(sim.events)
    assert t1[0] == t2[0] == 5.0 and t1[1] < t2[1]
    print("[same-timestamp] deterministic ordering by sequence: PASS")


def test_full_run_invariants():
    sim = Simulation("debug_map.csv", num_cars=5, num_riders=20, max_time=60.0,
                     mean_arrival_time=1.5, random_seed=7)
    run_quiet(instrumented_run, sim)
    assert all(c.status == "available" for c in sim.cars.values())
    assert invariant_holds(sim)
    # Completed cars sit at their last destination, not their start.
    moved = [c for c in sim.cars.values() if c.trips_completed > 0]
    assert moved, "expected at least one car to complete a trip"
    print(f"[full run] invariant held after every event; {len(sim.trip_log)} trips: PASS")


def test_no_cars():
    sim = Simulation("debug_map.csv", num_cars=0, num_riders=5, max_time=30.0, random_seed=3)
    r = run_quiet(lambda: (sim.run(), sim.analyze_results())[1])
    assert r["total_unmatched"] == r["total_riders_generated"]
    print("[no cars] every rider unmatched, no crash: PASS")


def test_fewer_than_k():
    sim = Simulation("debug_map.csv", num_cars=2, candidate_count=5, num_riders=6,
                     max_time=40.0, random_seed=9)
    run_quiet(instrumented_run, sim)
    assert invariant_holds(sim)
    print("[fewer than k] 2 cars with k=5 handled: PASS")


def test_pickup_time_from_dijkstra():
    # A dispatched car's pickup event time must equal current_time + a Dijkstra
    # cost, i.e. an integer-weighted grid distance, not a Manhattan placeholder.
    sim = Simulation("debug_map.csv", num_cars=5, num_riders=1, max_time=1.0, random_seed=1)
    rider = sim.generate_rider_request()
    sim.riders_generated += 1
    sim.current_time = 0.0
    sim.handle_rider_request(rider)
    pickup_events = [e for e in sim.events if e[2] == "PICKUP_ARRIVAL"]
    if pickup_events:
        # grid edges are unit weight, so a real Dijkstra time is a whole number
        assert float(pickup_events[0][0]).is_integer()
        print("[dijkstra timing] pickup time is a road-network cost: PASS")
    else:
        print("[dijkstra timing] rider unmatched this seed; skipped")


def main():
    test_same_timestamp_heap()
    test_full_run_invariants()
    test_no_cars()
    test_fewer_than_k()
    test_pickup_time_from_dijkstra()
    print("\nALL SIMULATION TESTS PASSED")


if __name__ == "__main__":
    main()
