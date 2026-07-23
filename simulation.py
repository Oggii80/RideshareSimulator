#simulation.py
"""
This class serves as the main controller for the entire simulation.
As of this submission, it currently holds collections of cars and riders
"""

import os
from graph import Graph

class Simulation:
    def __init__(self, map_filename):
        self.cars={}
        self.riders={}
        self.map = Graph()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.map.load_from_file(os.path.join(base_dir, map_filename))
        
