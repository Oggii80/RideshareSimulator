from pathfinding import find_shortest_path

class Car:
    """
    Represents a single car in the ride-sharing simulation
    """

    def __init__(self, car_id, initial_location):
        """
        Initialized a new Car object/

        Args:
            car_id(str): The unique identifier for the car.
            initial_location : Now an (x, y) coordinate
        """

        self.id = car_id
        self.location = initial_location
        self.status = 'available'
        self.passengers = []
        self.assigned_rider = None
        print(f"Car {self.id} created at location {self.location}.")

    def __str__(self):
      return f"Car{self.id} at {self.location} - Status: {self.status}"

    def calculate_route(self, destination, graph):
        path, total_cost = find_shortest_path(graph, self.location, destination)
        self.route = path
        self.route_time = total_cost
