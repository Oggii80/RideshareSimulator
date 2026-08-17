from pathfinding import find_shortest_path
from graph import find_nearest_vertex


class Car:
    def __init__(self, car_id, initial_location):
        self.id = car_id
        self.location = initial_location
        self.status = "available"
        self.assigned_rider = None
        self.route = None
        self.route_time = 0
        self.busy_start_time = None
        self.total_busy_time = 0
        self.trips_completed = 0

    def __str__(self):
        return f"Car {self.id} at {self.location} - Status: {self.status}"

    def calculate_route(self, destination, graph):
        start_vertex = find_nearest_vertex(self.location, graph.node_coordinates)
        end_vertex = find_nearest_vertex(destination, graph.node_coordinates)
        path, total_cost = find_shortest_path(graph, start_vertex, end_vertex)
        self.route = path
        self.route_time = total_cost
        return path, total_cost
