# Author: Lennon Conson

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory
import os
import tracemalloc
import time
import csv

tracemalloc.start()

model = ConcreteModel('Stochastic Military Port Selection Problem')
import csv
import datetime

packages_file = 'packages.csv'

# Initialize a packages dictionary
P = {}

# Encoded Packages Dictionary with Packages CSV file
with open(packages_file, mode='r') as file:
    reader = csv.DictReader(file)

    # Iterate over each row in the CSV file
    for row in reader:
        # Use the first column value as the key
        key = row.pop(reader.fieldnames[0])

        # Convert ISO date strings to datetime objects
        for date_column in ["RLD", "EAD", "LAD"]:
            if date_column in row:
                date_string = row[date_column]
                date_obj = datetime.date.fromisoformat(date_string)
                row[date_column] = date_obj
        # Store the remaining columns as a sub-dictionary
        P[key] = row

# Set of Origins
I = set()

#Set of Destinations
K = set()

# Iterate through all keys in the dictionary and add their values to the origin/detination set

#TODO there is a more eligant method that escapes me right now.
latestDate = datetime.date(2025, 12, 3)
earliestDate = datetime.date(2324, 4, 24)

for key in P:
    I.add(P[key]['Origin'])
    K.add(P[key]['Destination'])
    if P[key]['RLD'] < earliestDate:
        earliestDate = P[key]['RLD']
    if P[key]['LAD'] > latestDate:
        latestDate = P[key]['LAD']


T = []

indexDate = earliestDate

while indexDate <= latestDate:
    T.append(indexDate)
    indexDate += datetime.timedelta(days=1)

