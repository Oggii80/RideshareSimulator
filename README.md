# Efficient, Analyzed Ride-Sharing Simulator

## Overview

This project is a discrete-event simulation of a ride-sharing service. Riders
arrive dynamically on a road network, and each is matched to a car through a
two-stage search: a Quadtree finds the geographically nearest available cars,
then Dijkstra's algorithm chooses the one with the shortest actual road-network
travel time. It models the core efficiency problem of any on-demand dispatch
system — how well a fixed fleet serves an unpredictable stream of requests — and
reports fleet-level performance through both a metrics summary and an integrated
analytical image.

## Features

- **Event-driven simulation core** — a `heapq` event loop over four-field
  `(timestamp, sequence_number, event_type, data)` tuples with deterministic
  ordering of simultaneous events.
- **Dijkstra's algorithm** for optimal road-network pathfinding and true travel
  times.
- **Quadtree spatial index** for efficient nearest-available-car matching that
  prunes rather than scanning the whole fleet.
- **Two-stage matching pipeline** — Quadtree proposes geographic candidates,
  Dijkstra decides on road distance.
- **Dynamic rider generation** with exponential inter-arrival times and
  configurable stopping rules.
- **Synchronized availability index** — three structures kept consistent through
  two centralized methods.
- **Integrated visualization** — one PNG combining a map, a KPI panel, and charts.
- **Zone-based surge pricing** (optional extra credit) — prices demand hotspots
  via a per-zone request-to-driver ratio.

## Dependencies / Setup

Requires Python 3. The simulation core uses only the standard library; the PNG
visualization uses matplotlib. Install with:

    pip install -r requirements.txt

Run with `--no-plot` to skip the image and avoid the matplotlib dependency.

## How to Run

Run the full simulation and generate `simulation_summary.png`:

    python simulation.py --num-cars 15 --num-riders 250 --max-time 1000 \
        --mean-arrival 0.8 --random-seed 42

### Command-line options

| Option | Default | Meaning |
|---|---|---|
| `--map-file` | `city_map.csv` | Map to load. |
| `--num-cars` | 100 | Fleet size. |
| `--num-riders` | 200 | Cap on riders generated. |
| `--max-time` | 1000.0 | Stop generating new riders past this time. |
| `--candidate-count` | 5 | *k* — geographic candidates evaluated per request. |
| `--mean-arrival` | 2.0 | Mean inter-arrival gap (exponential). |
| `--random-seed` | none | Seed for reproducible runs. |
| `--output` | `simulation_summary.png` | Image path. |
| `--no-plot` | off | Metrics only, no image. |
| `--quiet` | off | Suppress the per-event log; show only final analysis. |
| `--surge` | off | Enable zone-based surge pricing. |
| `--surge-zones` | 4 | Grid resolution per axis for surge zones (4 = 4x4). |
| `--surge-sensitivity` | 0.1 | How sharply the multiplier responds to the ratio. |
| `--surge-cap` | 3.0 | Maximum surge multiplier. |

Rider generation stops when **either** `--num-riders` or `--max-time` is
reached. Trips already in progress finish afterward — the loop runs until the
event heap is empty, so no active trip is abandoned.

### Running the tests

    python test_dijkstra.py      # shortest path + no-route contract
    python test_quadtree.py      # find_k_nearest vs brute force; identity removal
    python test_simulation.py    # end-to-end invariants and correctness checks

`test_simulation.py` drives the event loop manually and asserts, after every
event, that the availability invariant holds and no busy car remains indexed. It
also checks same-timestamp determinism, the no-cars and fewer-than-*k* cases, and
that dispatch times come from Dijkstra.

## Project Structure

- `simulation.py` — the main simulation engine: event loop, availability index,
  rider generation, matching pipeline, metrics, and the command-line entry point.
- `quadtree.py` — the spatial index (`find_k_nearest`, identity-based `remove`).
- `graph.py` — the road network (adjacency list + node coordinates) and the
  `find_nearest_vertex` coordinate-to-vertex snap.
- `pathfinding.py` — Dijkstra's shortest-path implementation.
- `car.py`, `rider.py` — the simulation actors and their state.
- `visualization.py` — builds `simulation_summary.png`.
- `make_map.py` — utility that generates grid map files.
- `city_map.csv` — production map (10x10 grid). `debug_map.csv` — 5x5 debug map.
- `test_*.py` — the test / demonstration scripts.

---

## Reference: implementation details

### Map-file format

Each non-comment row is one road with seven fields:

    start_node_id,start_x,start_y,end_node_id,end_x,end_y,weight

Roads are stored in both directions, so the network is undirected. Lines
starting with `#` and blank lines are ignored. Regenerate a grid map with
`python make_map.py --cols 10 --rows 10 --spacing 100 --out city_map.csv`.

### Event model

The heap holds four-field `(timestamp, sequence_number, event_type, data)`
tuples. The sequence number (from `itertools.count()`) strictly increases, so
events sharing a timestamp are ordered by insertion and the heap never falls
through to comparing `Car`/`Rider` objects. Event types: `RIDER_REQUEST`,
`PICKUP_ARRIVAL`, `DROPOFF_ARRIVAL`.

### State transitions

    Car:   available -> en_route_to_pickup -> en_route_to_destination -> available
    Rider: waiting -> in_car -> completed

An unmatchable rider is marked `unmatched`; a trip with an unreachable
destination is marked `unsuccessful`.

### Matching workflow (Quadtree -> Dijkstra)

1. Build a query point from the rider's start location.
2. `find_k_nearest(query_point, k=candidate_count)` returns up to *k* nearest
   available cars by geography. Default *k* is 5 (`DEFAULT_CANDIDATE_COUNT`);
   change it with `--candidate-count`.
3. Snap the rider's start to a graph vertex once, then run Dijkstra from every
   candidate to it.
4. Select the reachable candidate with the smallest travel time; ties go to the
   nearer candidate. Pickup and trip times are Dijkstra costs, never straight-line
   placeholders.

### Availability synchronization

Three structures must always agree: `available_cars` (`car_id -> Car`),
`available_car_points` (`car_id -> the exact Point` in the tree), and
`available_car_quadtree`. All changes go through `add_available_car` (inserts
into the tree first, touches the dictionaries only on success) and
`remove_available_car` (removes the exact stored Point from the tree first, then
the dictionary entries, raising if the tree removal fails). This preserves:

    set(available_cars) == set(available_car_points) == cars indexed in the quadtree

A dispatched car is removed immediately and stays absent through pickup and the
trip; at drop-off it is reinserted at its new location with a fresh Point.

### Policy for unavailable cars and unreachable routes

- **No available cars / all candidates unreachable:** the rider is marked
  `unmatched` and counted; no waiting queue is used.
- **Unreachable destination at pickup:** the trip is marked `unsuccessful` and
  counted, the car's elapsed busy time is banked, its rider is cleared, and it is
  returned to availability at the pickup location. No event is scheduled at
  `float("inf")`.

### Reported metrics

- **Total riders generated / completed / unmatched** — request counts.
- **Average wait time** — mean `pickup_time - request_time` over completed trips.
- **Average trip duration** — mean `dropoff_time - pickup_time` over completed trips.
- **Driver utilization** — total busy time across all cars divided by
  (number of cars x simulation span), where the span is the final processed event
  time; busy time runs from dispatch through drop-off.
- **Trips per car** — completed trips divided by fleet size.

### Analytical visualization

`simulation_summary.png` combines a map of the road network with every car's
final position (colored by trips completed), a panel of the KPIs above, and two
charts: the rider wait-time distribution and a completed-vs-unmatched outcome bar.

### Surge pricing

Enabled with `--surge`. The map is partitioned into a `--surge-zones` x
`--surge-zones` grid over the coordinate extent. Each rider request increments a
running count for its origin zone, and at request time the zone's surge
multiplier is computed from the demand-to-supply ratio:

    multiplier = min(surge_cap, 1 + surge_sensitivity * (zone_requests / (drivers_in_zone + 1)))

On dispatch the rider receives a `fare` attribute equal to `BASE_FARE x
multiplier`, so trips originating in high-demand, low-supply zones cost more.
Enabling surge adds three metrics (average surge multiplier, maximum surge
multiplier, average fare) and leaves all other output unchanged.

Compare a run with and without surge (identical seed):

    python simulation.py --num-cars 15 --num-riders 250 --max-time 1000 --mean-arrival 0.8 --random-seed 42 --quiet --no-plot
    python simulation.py --num-cars 15 --num-riders 250 --max-time 1000 --mean-arrival 0.8 --random-seed 42 --surge --quiet --no-plot

Because fare is priced but does not feed back into dispatch (the fleet is fixed
and riders do not decline on price), surge here is descriptive: it prices demand
hotspots without altering rider wait time or driver utilization. Modeling a
supply or rider response to price would be the next step toward a behavioral
surge effect.
