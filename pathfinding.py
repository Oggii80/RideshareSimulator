#pathfinding.py

import heapq


def find_shortest_path(graph, start_node, end_node):
    distances = {}
    distances[start_node] = 0
    predecessors = {}
    priority_queue = [(0, start_node)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_distance > distances.get(current_node, float('inf')):
            continue


        for neighbor, weight in graph.adjacency_list.get(current_node, []):
            candidate = current_distance + weight

            if candidate < distances.get(neighbor, float('inf')):
                distances[neighbor] = candidate
                predecessors[neighbor] = current_node
                heapq.heappush(priority_queue, (candidate, neighbor))

    if end_node not in distances:
        return (None, float('inf'))
    
    path = []
    node = end_node
    while node is not None:
        path.append(node)
        node = predecessors.get(node)
    path.reverse()
    return (path, distances[end_node])
 
