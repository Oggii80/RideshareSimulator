# test_quadtree.py
import random
import math
from quadtree import Point, Rectangle, Quadtree


def bf_k_nearest(points, query, k):
    ordered = sorted(points, key=lambda p: math.dist((query.x, query.y), (p.x, p.y)))
    return ordered[:k]


def dseq(q, pts):
    return [round(math.dist((q.x, q.y), (p.x, p.y)), 6) for p in pts]


def main():
    random.seed(42)
    boundary = Rectangle(0, 0, 1000, 1000)
    qt = Quadtree(boundary, capacity=4)

    points = []
    for i in range(3000):
        p = Point(random.uniform(0, 1000), random.uniform(0, 1000), data=f"car_{i}")
        points.append(p)
        qt.insert(p)

    # k-nearest matches brute force by distance across many queries.
    for _ in range(200):
        q = Point(random.uniform(0, 1000), random.uniform(0, 1000))
        got = qt.find_k_nearest(q, k=5)
        exp = bf_k_nearest(points, q, 5)
        assert dseq(q, got) == dseq(q, exp), "k-NN disagrees with brute force"
        assert dseq(q, got) == sorted(dseq(q, got)), "results not nearest-to-farthest"
    print("find_k_nearest matches brute force and is correctly ordered.")

    # Edge cases.
    assert Quadtree(boundary).find_k_nearest(Point(1, 1)) == []
    try:
        qt.find_k_nearest(Point(1, 1), k=0)
        raise AssertionError("k<=0 should raise")
    except ValueError:
        pass
    print("Empty tree and nonpositive-k cases handled.")

    # Identity-based removal with two cars at identical coordinates.
    rq = Quadtree(boundary, capacity=4)
    a = Point(100, 100, "A")
    b = Point(100, 100, "B")
    for p in (a, b):
        rq.insert(p)
    assert rq.remove(a) is True
    remaining = rq.find_k_nearest(Point(100, 100), k=5)
    assert any(p is b for p in remaining) and all(p is not a for p in remaining)
    assert rq.remove(a) is False           # already gone
    assert rq.remove(Point(100, 100)) is False  # never inserted
    print("remove() uses object identity and handles duplicate coordinates.")

    print("\nALL QUADTREE TESTS PASSED")


if __name__ == "__main__":
    main()
