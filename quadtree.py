# quadtree.py

import heapq
import itertools
import math


class Point:
    def __init__(self, x, y, data=None):
        self.x = x
        self.y = y
        self.data = data

    def __repr__(self):
        return f"Point ({self.x:.2f}, {self.y:.2f}, data={self.data})"


class Rectangle:
    # (x, y) is the top-left corner.
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, point):
        return (self.x <= point.x <= self.x + self.width and
                self.y <= point.y <= self.y + self.height)

    def distance_to_point(self, point):
        # Shortest distance from point to this rectangle; 0 if inside (enables pruning).
        dx = max(self.x - point.x, 0, point.x - (self.x + self.width))
        dy = max(self.y - point.y, 0, point.y - (self.y + self.height))
        return math.sqrt(dx * dx + dy * dy)


class QuadtreeNode:
    def __init__(self, boundary, capacity=4):
        self.boundary = boundary
        self.capacity = capacity
        self.points = []
        self.divided = False
        self.northwest = None
        self.northeast = None
        self.southwest = None
        self.southeast = None

    def _children(self):
        return (self.northwest, self.northeast, self.southwest, self.southeast)

    def subdivide(self):
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.width / 2
        h = self.boundary.height / 2

        self.northwest = QuadtreeNode(Rectangle(x, y, w, h), self.capacity)
        self.northeast = QuadtreeNode(Rectangle(x + w, y, w, h), self.capacity)
        self.southwest = QuadtreeNode(Rectangle(x, y + h, w, h), self.capacity)
        self.southeast = QuadtreeNode(Rectangle(x + w, y + h, w, h), self.capacity)
        self.divided = True

        for p in self.points:
            self._insert_into_children(p)
        self.points = []

    def _insert_into_children(self, point):
        return (self.northwest.insert(point) or
                self.northeast.insert(point) or
                self.southwest.insert(point) or
                self.southeast.insert(point))

    def insert(self, point):
        if not self.boundary.contains(point):
            return False

        if not self.divided:
            if len(self.points) < self.capacity:
                self.points.append(point)
                return True
            self.subdivide()

        return self._insert_into_children(point)

    def find_nearest(self, query_point, best=None):
        if best is None:
            best = {"point": None, "distance": float("inf")}

        if self.boundary.distance_to_point(query_point) > best["distance"]:
            return best

        for p in self.points:
            d = math.dist((query_point.x, query_point.y), (p.x, p.y))
            if d < best["distance"]:
                best["distance"] = d
                best["point"] = p

        if self.divided:
            children = list(self._children())
            children.sort(key=lambda c: c.boundary.distance_to_point(query_point))
            for child in children:
                child.find_nearest(query_point, best)

        return best

    def _knn(self, query_point, k, heap, counter):
        # heap is a size-k MAX-heap keyed on negative distance, so heap[0]
        # is the current farthest keeper. Prune any region that cannot beat it.
        if len(heap) == k:
            farthest = -heap[0][0]
            if self.boundary.distance_to_point(query_point) > farthest:
                return

        for p in self.points:
            d = math.dist((query_point.x, query_point.y), (p.x, p.y))
            if len(heap) < k:
                heapq.heappush(heap, (-d, next(counter), p))
            elif d < -heap[0][0]:
                heapq.heapreplace(heap, (-d, next(counter), p))

        if self.divided:
            children = list(self._children())
            children.sort(key=lambda c: c.boundary.distance_to_point(query_point))
            for child in children:
                child._knn(query_point, k, heap, counter)

    def remove(self, point):
        if not self.boundary.contains(point):
            return False

        if not self.divided:
            for i, stored_point in enumerate(self.points):
                if stored_point is point:   # identity, not coordinate equality
                    del self.points[i]
                    return True
            return False

        # Inclusive bounds mean a point on a split line can sit in more than one
        # child, so try every child whose boundary contains it until identity hits.
        for child in self._children():
            if child.boundary.contains(point) and child.remove(point):
                return True
        return False


class Quadtree:
    def __init__(self, boundary, capacity=4):
        self.boundary = boundary
        self.root = QuadtreeNode(boundary, capacity)

    def insert(self, point):
        return self.root.insert(point)

    def find_nearest(self, query_point):
        return self.root.find_nearest(query_point)["point"]

    def find_k_nearest(self, query_point, k=5):
        if k <= 0:
            raise ValueError("k must be a positive integer.")

        heap = []
        counter = itertools.count()   # unique tie-breaker; heap never compares Points
        self.root._knn(query_point, k, heap, counter)

        # Heap holds up to k items keyed on negative distance; sort ascending by
        # true distance so the result is nearest-to-farthest.
        ordered = sorted(heap, key=lambda item: -item[0])
        return [item[2] for item in ordered]

    def remove(self, point):
        return self.root.remove(point)
