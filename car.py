class Car:
    """
    Represents a single car in the ride-sharing simulation
    """

    def __init__(self, car_id, initial_location):
        """
        Initialized a new Car object/

        Args:
            car_id(str): The unique identifier for the car.
            initial_location(tuple): The starting (x,y) coords.
        """

        self.id = car_id
        self.location = initial_location
        self.status = 'available'
        self.passengers = []
        print(f"Car {self.id} created at location {self.location}.")

    def __str__(self):
      return f"Car{self.id} at {self.location} - Status: {self.status}"

