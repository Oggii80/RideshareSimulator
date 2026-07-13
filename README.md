# RideshareSimulator
"""
First Iteration of Rideshare Simulator

Purpose/Design
This project is the foundational milestone for a ride-sharing simulator, focused on object-oriented design before any pathfinding or optimization logic is introduced. The design defines three core classes (Car, Rider, and Simulation) each in its own module to keep state and behavior encapsulated and the codebase modular. The Simulation class stores its Car and Rider objects in dictionaries keyed by ID, chosen to support O(1) lookups when driver-matching logic is added in later milestones.

How to Run
Ensure Python 3 is installed (python --version).
Clone the repository and navigate into its directory.

Run the test script:
python main.py

The script instantiates a Car, a Rider, and a Simulation, registers the objects with the simulation, and prints each one to demonstrate the class structure and __str__ output.
Dependencies
Not Applicable (Native libraries only).
"""