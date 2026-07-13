#test_script.py

from car import Car
from rider import Rider
from simulation import Simulation

def main():
    car=Car("CAR001",(10, 5))
    rider=Rider("Rider_A", (1, 2), (20, 15))
    sim = Simulation()

    sim.cars[car.id] = car
    sim.riders[rider.id] = rider

    print(car)
    print(rider)
    print()

    print(f"Simulation tracking {len(sim.cars)} car(s), {len(sim.riders)} rider(s)")
    for car_id, car_obj in sim.cars.items():
        print(f" [{car_id}] -> {car_obj}")
    for rider_id, rider_obj in sim.riders.items():
        print(f" [{rider_id}] -> {rider_obj}")

if __name__ == "__main__":
    main()
