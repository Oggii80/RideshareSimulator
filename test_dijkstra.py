# test_dijkstra.py
import os
from pathfinding import find_shortest_path
from graph import Graph, find_nearest_vertex


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    graph = Graph()
    graph.load_map_data(os.path.join(base_dir, "city_map.csv"))

    a = find_nearest_vertex((0.0, 0.0), graph.node_coordinates)
    b = find_nearest_vertex((900.0, 900.0), graph.node_coordinates)
    path, cost = find_shortest_path(graph, a, b)
    print(f"{a} -> {b}: {path}, cost {cost}")

    path, cost = find_shortest_path(graph, a, "DOES_NOT_EXIST")
    print(f"Impossible route: {path}, cost {cost}")
    assert path is None and cost == float("inf")
    print("Dijkstra no-route contract holds.")


if __name__ == "__main__":
    main()
