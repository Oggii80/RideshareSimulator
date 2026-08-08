#test_script.py

from car import Car
from rider import Rider
from simulation import Simulation


def main():
    sim = Simulation("map.csv")
    print("Loaded Map: ")
    print(sim.map)

    # Two cars starting in different corners of the map.
    cars = [
        Car("CAR001", (10, 5)),
        Car("CAR002", (80, 80)),
    ]

    # Three riders. request_time controls when each enters the event queue.
    # Rider_C requests after CAR001 has finished Rider_A, so the same car
    # is reused rather than a third car being needed.
    riders = [
        Rider("Rider_A", (1, 2),   (20, 15), request_time=0),
        Rider("Rider_B", (75, 70), (90, 90), request_time=1),
        Rider("Rider_C", (25, 20), (40, 40), request_time=5),
    ]

    for car in cars:
        sim.cars[car.id] = car
    for rider in riders:
        sim.riders[rider.id] = rider

    print(f"Simulation tracking {len(sim.cars)} car(s), {len(sim.riders)} rider(s)")
    for car_id, car_obj in sim.cars.items():
        print(f" [{car_id}] -> {car_obj}")
    for rider_id, rider_obj in sim.riders.items():
        print(f" [{rider_id}] -> {rider_obj}")

    print("\n--- SIMULATION START ---")
    sim.run()
    print("--- SIMULATION END ---")


if __name__ == "__main__":
    main()
