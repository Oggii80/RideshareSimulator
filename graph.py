#graph.py

import collections


class Graph:
    def __init__(self):
        self.adjacency_list = collections.defaultdict(list)
        self.node_coordinates = {}

    def add_edge(self, start_node, end_node, weight):
        self.adjacency_list[start_node].append((end_node, weight))

    def load_map_data(self, filename):
        # Each non-comment row is one road:
        # start_id,start_x,start_y,end_id,end_x,end_y,weight
        with open(filename, "r") as file:
            for line in file:
                if line.startswith("#") or not line.strip():
                    continue

                parts = line.strip().split(",")
                (
                    start_id,
                    start_x,
                    start_y,
                    end_id,
                    end_x,
                    end_y,
                    weight,
                ) = parts

                self.node_coordinates[start_id] = (float(start_x), float(start_y))
                self.node_coordinates[end_id] = (float(end_x), float(end_y))

                w = float(weight)
                self.adjacency_list[start_id].append((end_id, w))
                self.adjacency_list[end_id].append((start_id, w))

    def __str__(self):
        result = ""
        for node, edges in self.adjacency_list.items():
            result += f"{node} -> {edges}\n"
        return result


def find_nearest_vertex(point, node_coordinates):
    # Return the graph-node ID geographically closest to an (x, y) point.
    if not node_coordinates:
        raise ValueError("No graph vertices loaded; cannot snap coordinate.")

    px, py = point
    best_id = None
    best_sq = float("inf")
    for node_id, (nx, ny) in node_coordinates.items():
        sq = (nx - px) ** 2 + (ny - py) ** 2   # squared distance avoids sqrt
        if sq < best_sq:
            best_sq = sq
            best_id = node_id
    return best_id
