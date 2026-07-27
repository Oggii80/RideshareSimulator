A ride-sharing simulation built around object-oriented design and graph-based pathfinding. Cars and riders exist in a weighted road network, and cars can calculate the fastest route between any two locations using Dijkstra's algorithm.

Purpose / Design

The project is organized around three core classes — Car, Rider, and Simulation — each in its own module, to keep state and behavior encapsulated and the codebase modular. The road network is represented by a Graph class using an adjacency list.

The Simulation class stores its Car and Rider objects in dictionaries keyed by ID, chosen to support O(1) lookups when driver-matching logic is added in later milestones.

With this milestone, cars are no longer just placed in the world — they can navigate it. Each Car can compute the optimal route from its current location to a destination and remember that plan.

Pathfinding

Route-finding is implemented in pathfinding.py as a standalone function:

find_shortest_path(graph, start_node, end_node)

It implements Dijkstra's algorithm to find the lowest-cost route through the weighted graph. It returns a tuple of the path (a list of nodes) and the total travel cost — for example (['A', 'C', 'D'], 4). If no route exists between the two nodes, it returns (None, float('inf')).

The algorithm uses a min-heap priority queue (Python's heapq) to decide which node to visit next. The heap always hands back the unvisited node with the smallest known distance from the start, which is what keeps Dijkstra efficient — the algorithm never wastes work exploring a longer route when a shorter one is still pending. Because heapq has no operation to update an entry already in the queue, a shorter path to an already-queued node is handled by pushing a second entry and discarding the outdated one when it surfaces.

The path itself is reconstructed from a predecessors dictionary that records, for each node, which node it was reached from on the shortest path. Once the destination is reached, the path is rebuilt by walking predecessors backward from the destination to the start and then reversing the result.

Integration with the Car class

Pathfinding is wired into the Car class through a method:

Car.calculate_route(destination, graph)

This method calls find_shortest_path, using the car's current self.location as the start node and the passed-in destination as the end node. It stores the results on the car as self.route and self.route_time, so the car "remembers" its planned route. The method calls the shared find_shortest_path function rather than reimplementing the algorithm, keeping a single tested implementation of the pathfinding logic.

Map File Format

The road network is loaded from map.csv. Each line is a single directed edge:

start_node,end_node,weight

For example:

A,B,5
B,A,5
A,C,3
C,A,3

Each connection is listed in both directions so the network behaves as an undirected road map (a road from A to B is also a road from B to A).

How to Run

Requires Python 3 (python --version to check).

Clone the repository and navigate into the project directory.

Run the pathfinding test in isolation:

python test_dijkstra.py

This loads the graph from map.csv, runs find_shortest_path on a known route (A to D) and on an impossible route (A to Z), and prints the results, verifying both the shortest-path logic and the no-path case.

Run the object-structure demo:

python test_script.py

This instantiates a Car, a Rider, and a Simulation, registers the objects with the simulation, and prints each one to demonstrate the class structure.

The scripts locate map.csv relative to their own file location, so they can be run from any working directory.

Dependencies

None beyond the Python standard library. The project uses only heapq and os, both of which ship with Python — nothing to install.
