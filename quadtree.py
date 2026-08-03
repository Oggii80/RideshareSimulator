# quadtree.py

import math

# Class for each point
class Point: 
    def __init__(self, x, y, data=None):
        self.x = x
        self.y = y
        self.data = data

    def __repr__(self):
        return f"Point ({self.x:2f}, {self.y:2f}, data={self.data})"

# Class for the Rectangle where (x, y) is the top-left corner
class Rectangle:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self. height = height

    def contains(self, point):
        return(self.x <= point.x <= self.x + self.width and
            self.y <= point.y <= self.y + self.height)

    def distance_to_point(self, point):
        #shortest distance from `point` to this particular rectangle.
        #returns 0 if inside so that we can do some pruning
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

    def subdivide(self):
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.width/2
        h = self.boundary.height/2

        self.northwest = QuadtreeNode(Rectangle(x, y, w, h), self.capacity)
        self.northeast = QuadtreeNode(Rectangle(x+w, y, w, h), self.capacity)
        self.southwest = QuadtreeNode(Rectangle(x, y+h, w, h), self.capacity)
        self.southeast = QuadtreeNode(Rectangle(x+w, y+h, w, h), self.capacity)
        self.divided = True

        #push points down to the new children
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
            best = {"Point": None, "distance": float("inf")}

        #Prune if closes possible point in region is further than point already found. Skips whole branch
        if self.boundary.distance_to_point(query_point) > best["distance"]:
            return best

        #check points helpd at this node
        for p in self.points:
            d=math.dist((query_point.x, query_point.y), (p.x, p.y))
            if d < best["distance"]:
                best["distance"] = d
                best["point"] = p

        # Recurse best-first

        if self.divided:
            children = [self.northwest, self.northeast, self. southwest, self.southeast]
            children.sort(key=lambda c: c.boundary.distance_to_point(query_point))
            for child in children:
                child.find_nearest(query_point, best)

        return best

class Quadtree:
    def __init__(self, boundary, capacity=4):
        self.boundary=boundary
        self.root=QuadtreeNode(boundary, capacity)

    def insert(self, point):
        return self.root.insert(point)

    def find_nearest(self, query_point):
        return self.root.find_nearest(query_point)["point"]


