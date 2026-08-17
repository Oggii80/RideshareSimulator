# Efficient, Analyzed Ride-Sharing Simulator

A discrete-event ride-sharing simulation. Riders arrive dynamically on a road
network; each is matched to a car using a two-stage search — a Quadtree finds
the geographically nearest available cars, and Dijkstra's algorithm picks the
one with the shortest actual road-network travel time. The run produces a
metrics summary and an integrated analytical image.

## Components

- **Graph** (`graph.py`) — road topology (weighted adjacency list) plus node
  geometry (`node_coordinates`), loaded from one unified map file.
- **Quadtree** (`quadtree.py`) — spatial index of available cars; returns up to
  *k* nearest candidates and supports identity-based removal.
- **Dijkstra** (`pathfinding.py`) — shortest road route and travel time.
- **Simulation** (`simulation.py`) — the event engine, availability index,
  rider generation, matching pipeline, and metrics.
- **Visualization** (`visualization.py`) — builds `simulation_summary.png`.

## Installation

Requires Python 3. The simulation core uses only the standard library. The PNG
visualization requires matplotlib:

    pip install matplotlib

Run the simulation with `--no-plot` to skip the image and avoid the matplotlib
dependency entirely.

## Running the simulation

    python simulation.py --num-cars 15 --num-riders 250 --max-time 1000 \
        --mean-arrival 0.8 --random-seed 42

### Command-line options

| Option | Default | Meaning |
|---|---|---|
| `--map-file` | `city_map.csv` | Map to load. |
| `--num-cars` | 100 | Fleet size. |
| `--num-riders` | 200 | Cap on riders generated. |
| `--max-time` | 1000.0 | Stop generating new riders past this time. |
| `--candidate-count` | 5 | *k* — geographic candidates per request. |
| `--mean-arrival` | 2.0 | Mean inter-arrival gap (exponential). |
| `--random-seed` | none | Seed for reproducible runs. |
| `--output` | `simulation_summary.png` | Image path. |
| `--no-plot` | off | Metrics only, no image. |

Rider generation stops when **either** `--num-riders` or `--max-time` is
reached. Trips already in progress continue to completion after generation
stops — the main loop runs until the event heap is empty, so no active trip is
abandoned.

## Map-file format

Each non-comment row is one road with seven fields:

    start_node_id,start_x,start_y,end_node_id,end_x,end_y,weight

Roads are stored in both directions, so the network behaves as undirected. Lines
beginning with `#` and blank lines are ignored. `make_map.py` generates a grid
map: `python make_map.py --cols 10 --rows 10 --spacing 100 --out city_map.csv`.

## Event model

The event heap holds four-field tuples:

    (timestamp, sequence_number, event_type, data)

The sequence number (from `itertools.count()`) is a strictly increasing
tie-breaker, so two events sharing a timestamp are ordered by insertion and the
heap never falls through to comparing `Car`/`Rider` objects. Event types:
`RIDER_REQUEST`, `PICKUP_ARRIVAL`, `DROPOFF_ARRIVAL`.

## State transitions

    Car:   available -> en_route_to_pickup -> en_route_to_destination -> available
    Rider: waiting -> in_car -> completed

A rider that cannot be matched is marked `unmatched`; a trip whose destination
is unreachable is marked `unsuccessful`.

## Matching workflow (Quadtree -> Dijkstra)

1. Build a query point from the rider's start location.
2. `find_k_nearest(query_point, k=candidate_count)` returns up to *k* nearest
   available cars by straight-line geography. Default *k* is 5
   (`DEFAULT_CANDIDATE_COUNT`); change it with `--candidate-count`.
3. Snap the rider's start to a graph vertex once, then run Dijkstra from every
   candidate to that vertex.
4. Select the reachable candidate with the smallest road-network travel time.
   Ties go to the nearer (earlier-returned) candidate. Geography proposes; road
   distance decides. Pickup and trip times always come from Dijkstra, never a
   straight-line placeholder.

## Availability synchronization

Three structures track available cars and must always agree:

- `available_cars` — `car_id -> Car`.
- `available_car_points` — `car_id -> the exact Point` stored in the tree.
- `available_car_quadtree` — the spatial index.

All changes go through two methods. `add_available_car` inserts into the tree
first and touches the dictionaries only on success, so a boundary rejection
leaves nothing half-registered. `remove_available_car` removes the exact stored
`Point` from the tree first and mutates the dictionaries only after; if the tree
removal fails it raises rather than letting the structures drift. This preserves:

    set(available_cars) == set(available_car_points) == cars indexed in the quadtree

A dispatched car is removed immediately and stays absent through pickup and the
passenger trip; on drop-off it is reinserted at its **new** location with a fresh
`Point`.

## Unavailable cars and unreachable routes

- **No available cars / all candidates unreachable:** the rider is marked
  `unmatched` and counted; no waiting queue is used.
- **Unreachable destination at pickup:** the trip is marked `unsuccessful` and
  counted, the car's elapsed busy time is banked, its rider is cleared, and it is
  returned to availability at the pickup location. No event is ever scheduled at
  `float("inf")`.

## Reported metrics

- **Total riders generated** — requests created.
- **Total completed** — trips that reached drop-off.
- **Total unmatched/unsuccessful** — requests with no car or no route.
- **Average wait time** — mean of `pickup_time - request_time` over completed trips.
- **Average trip duration** — mean of `dropoff_time - pickup_time` over completed trips.
- **Driver utilization** — total busy time across all cars divided by
  (number of cars x simulation span), where the span is the final processed event
  time. Busy time runs from dispatch through drop-off.
- **Trips per car** — completed trips divided by fleet size.

## Analytical visualization

`simulation_summary.png` combines three things in one image: a map of the road
network with the final position of every car (colored by trips completed), a
panel of the KPIs above, and two charts — the rider wait-time distribution and a
completed-vs-unmatched outcome bar.

## Running the tests

    python test_dijkstra.py      # shortest path + no-route contract
    python test_quadtree.py      # find_k_nearest vs brute force; identity removal
    python test_simulation.py    # end-to-end invariants and correctness checks

`test_simulation.py` drives the event loop manually and asserts, after every
event, that the availability invariant holds and that no busy car remains in the
index. It also checks same-timestamp determinism, the no-cars and fewer-than-*k*
cases, and that dispatch times come from Dijkstra.
