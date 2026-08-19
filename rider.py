"""Represents a single rider in the simulation."""


class Rider:
    def __init__(self, rider_id, pickup_location, dropoff_location):
        # Locations are (x, y) coordinate tuples.
        self.id = rider_id
        self.start_location = pickup_location
        self.destination = dropoff_location
        self.status = "waiting"

        # Timing fields stay None until the relevant event sets them, so
        # "if request_time is None" reliably means "not yet requested".
        self.request_time = None
        self.pickup_time = None
        self.dropoff_time = None

        # Populated only when surge pricing is enabled.
        self.fare = None
        self.surge_multiplier = None

    def __str__(self):
        return (
            f"Rider {self.id} at {self.start_location}"
            f" waiting for ride to {self.destination}"
        )
