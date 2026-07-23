#graph.py

class Graph:
    def __init__(self):
        self.adjacency_list = {}

    def add_edge(self, start_node, end_node, weight):
        if start_node not in self.adjacency_list:
                self.adjacency_list[start_node] = []
        self.adjacency_list[start_node].append((end_node, weight))

    def load_from_file(self, filename):
        with open(filename) as f:
            for line in f:
                parts = line.strip().split(',')
                start_node, end_node, weight= parts
                self.add_edge(start_node, end_node, int(weight))

    def __str__(self):
        result = ""
        for node, edges in self.adjacency_list.items():
            result += f"{node} -> {edges}\n"
        return result    
