from pathfinding import find_shortest_path
from graph import find_nearest_vertex


class Car:
    """Represents a single car in the ride-sharing simulation."""

    def __init__(self, car_id, initial_location):
        # car_id: unique str. initial_location: (x, y) coordinate tuple.
        self.id = car_id
        self.location = initial_location
        self.status = "available"
        self.assigned_rider = None

        # Route the car is currently following, plus its Dijkstra cost.
        self.route = None
        self.route_time = 0

        # Utilization bookkeeping.
        self.busy_start_time = None
        self.total_busy_time = 0
        self.trips_completed = 0

    def __str__(self):
        return f"Car {self.id} at {self.location} - Status: {self.status}"

    def calculate_route(self, destination, graph):
        # Snap both coordinate endpoints to graph vertices, then run Dijkstra.
        start_vertex = find_nearest_vertex(self.location, graph.node_coordinates)
        end_vertex = find_nearest_vertex(destination, graph.node_coordinates)
        path, total_cost = find_shortest_path(graph, start_vertex, end_vertex)
        self.route = path
        self.route_time = total_cost
        return path, total_cost
