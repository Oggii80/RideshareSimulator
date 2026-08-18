# visualization.py
"""
Builds the single integrated analytical image (simulation_summary.png):
a map of final car positions, a metrics panel, and two charts.
Run the simulation first, then pass it here.
"""

import matplotlib
matplotlib.use("Agg")   # headless backend so it works without a display
import matplotlib.pyplot as plt


def create_summary(sim, results, filename="simulation_summary.png"):
    fig = plt.figure(figsize=(16, 9))
    grid = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

    # ----- map: roads + final car positions -----
    ax_map = fig.add_subplot(grid[:, 0:2])
    for start_id, edges in sim.map.adjacency_list.items():
        sx, sy = sim.map.node_coordinates[start_id]
        for end_id, _weight in edges:
            ex, ey = sim.map.node_coordinates[end_id]
            ax_map.plot([sx, ex], [sy, ey], color="0.85", linewidth=1, zorder=1)

    car_x = [c.location[0] for c in sim.cars.values()]
    car_y = [c.location[1] for c in sim.cars.values()]
    car_trips = [c.trips_completed for c in sim.cars.values()]
    if car_x:
        sc = ax_map.scatter(car_x, car_y, c=car_trips, cmap="viridis",
                            s=90, edgecolors="black", linewidths=0.6, zorder=3)
        cbar = fig.colorbar(sc, ax=ax_map, fraction=0.046, pad=0.04)
        cbar.set_label("Trips completed by car")

    ax_map.set_title("Final car positions on the road network")
    ax_map.set_xlabel("x")
    ax_map.set_ylabel("y")
    ax_map.set_aspect("equal", adjustable="datalim")

    # ----- metrics panel -----
    ax_metrics = fig.add_subplot(grid[0, 2])
    ax_metrics.axis("off")
    lines = [
        "KEY PERFORMANCE INDICATORS",
        "",
        f"Riders generated:   {results['total_riders_generated']}",
        f"Trips completed:    {results['total_completed']}",
        f"Unmatched:          {results['total_unmatched']}",
        f"Avg wait time:      {results['average_wait_time']:.2f}",
        f"Avg trip duration:  {results['average_trip_duration']:.2f}",
        f"Driver utilization: {results['driver_utilization_percent']:.1f}%",
        f"Trips per car:      {results['trips_per_car']:.2f}",
    ]
    ax_metrics.text(0.0, 1.0, "\n".join(lines), va="top", ha="left",
                    family="monospace", fontsize=11, transform=ax_metrics.transAxes)

    # ----- chart 1: rider wait-time distribution -----
    ax_wait = fig.add_subplot(grid[1, 2])
    waits = [t["wait_time"] for t in sim.trip_log]
    if waits:
        ax_wait.hist(waits, bins=15, color="steelblue", edgecolor="black")
    ax_wait.set_title("Rider wait-time distribution")
    ax_wait.set_xlabel("Wait time")
    ax_wait.set_ylabel("Riders")

    # ----- chart 2: completed vs unmatched -----
    ax_out = fig.add_subplot(grid[2, 2])
    ax_out.bar(["Completed", "Unmatched"],
               [results["total_completed"], results["total_unmatched"]],
               color=["seagreen", "indianred"], edgecolor="black")
    ax_out.set_title("Request outcomes")
    ax_out.set_ylabel("Riders")

    fig.suptitle("Ride-Sharing Simulation Summary", fontsize=16, y=0.98)
    fig.savefig(filename, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return filename
