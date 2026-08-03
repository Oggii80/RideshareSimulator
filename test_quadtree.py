import random
import math
from quadtree import Point, Rectangle, Quadtree


def brute_force_nearest(points, query):
    #Check every point, keep the closest.
    best_point = None
    best_dist = float("inf")
    for p in points:
        d = math.dist((query.x, query.y), (p.x, p.y))
        if d < best_dist:
            best_dist = d
            best_point = p
    return best_point


def main():
    random.seed(42)

    boundary = Rectangle(0, 0, 1000, 1000)
    qt = Quadtree(boundary, capacity=4)

    points = []
    for i in range(5000):
        p = Point(random.uniform(0, 1000), random.uniform(0, 1000), data=f"car_{i}")
        points.append(p)
        qt.insert(p)

    query = Point(random.uniform(0, 1000), random.uniform(0, 1000))

    qt_result = qt.find_nearest(query)
    bf_result = brute_force_nearest(points, query)

    qt_dist = math.dist((query.x, query.y), (qt_result.x, qt_result.y))
    bf_dist = math.dist((query.x, query.y), (bf_result.x, bf_result.y))

    print(f"Query point:         ({query.x:.2f}, {query.y:.2f})")
    print(f"Quadtree nearest:    {qt_result}  (distance {qt_dist:.4f})")
    print(f"Brute-force nearest: {bf_result}  (distance {bf_dist:.4f})")

    # Compare based on distance
    assert math.isclose(qt_dist, bf_dist), \
        "MISMATCH: Quadtree and brute-force disagree!"
    print("\nSUCCESS: Quadtree result matches brute-force result.")


if __name__ == "__main__":
    main()
