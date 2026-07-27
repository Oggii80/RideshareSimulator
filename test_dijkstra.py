import os
from pathfinding import find_shortest_path
from graph import Graph

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    graph = Graph()
    graph.load_from_file(os.path.join(base_dir, "map.csv"))
    
    path, total_cost = find_shortest_path(graph, "A", "D")
    print(f"A - D: {path}, distance {total_cost}")
    
    path, total_cost = find_shortest_path(graph, "A", "Z")
    print(f"Testing for impossible route: Route 'A' - 'Z': {path}, distance {total_cost}")

if __name__ == "__main__":
    main()
