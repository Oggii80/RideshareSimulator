#rider.py
"""
Represent a single rider in the simulation
"""

class Rider:
    def __init__(self, rider_id, pickup_location, dropoff_location, request_time=0):
        self.id=rider_id
        self.start_location=pickup_location
        self.destination=dropoff_location
        self.status="waiting"
        self.request_time=request_time
        self.pickup_time=0
        self.dropoff_time=0

    def __str__(self):
        return(
            f"Rider {self.id} at {self.start_location}"
            f" waiting for ride to {self.destination}"
        )
