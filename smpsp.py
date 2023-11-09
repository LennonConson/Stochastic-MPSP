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

# TODO error handeling for encoding packages.
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

# Setup intracontential travel time durations
# TODO Add error handeling
# TODO Delete useless entries
c = {}
J = set()

intraC_file = 'intracontinental.times.csv'

with open(intraC_file, 'r') as file:
    csv_reader = csv.reader(file)

    next(csv_reader)

    for row in csv_reader:
        key = (row[0], row[1])
        value = float(row[2])
        c[key] = value
        J.add(row[1])

print("Check to make sure there are no slight variations of spelling in list of Origins.")
print("")
print("Origins")
print("-------------------")
for i in I:
    print(i)

print("Check to make sure there are no slight variations of spelling in list of SPOE.")
print("")
print("SPOE")
print("-------------------")
for j in J:
    print(j)

print("Check to make sure there are no slight variations of spelling in list of SPOD.")
print("")
print("SPOD")
print("-------------------")
for k in K:
    print(k)

# Decision Variables
model.x = Var(P.keys(), J, T, domain=Binary)

print("")
print("Dimension of x_pjt is " + str(len(model.x)))


# Objective
# TODO Current Objective not very useful
def obj_rule(model):
    return sum(c[P[p]['Origin'],j ] * model.x[p,j,t] for p in P.keys() for j in J for t in T)

model.obj = pyo.Objective(rule=obj_rule)

# Constraints

# Ensure a package only goes through a single port
def singlePort(model, p):
    return sum(model.x[p, j, t] for j in J for t in T) == 1

model.constSinglePort = Constraint(P.keys(), rule=singlePort)

print("Dimension of Single Port Constraint is " + str(len(model.constSinglePort)))

# Ensure a package doesn't leave origin before the RLD
def rld(model,p):

    eldDates = []

    indexDate = earliestDate

    while indexDate < latestDate:
        eldDates.append(indexDate)
        indexDate += datetime.timedelta(days=1)


    lastDate = P[p]['RLD']
    return sum(model.x[p,j,t] for j in J for t in eldDates) == 0

model.contRLD = Constraint(P.keys(), rule=rld)

solver = SolverFactory('cplex')
results = solver.solve(model)

print("Optimal solution found with objective value:", model.obj())

routes = []

for p in P.keys():
    for j in J:
        for t in T:
            i = P[p]['Origin']
            if model.x[p, j, t].value == 1:
                routes.append((p,i, t, j, c[(i,j)]))

routes_file = 'routes.csv'
with open(routes_file, 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(['Package ID', 'Origin', 'Depart Origin','SPOE','Travel Time to SPOE'])
    csv_writer.writerows(routes)
print("Optimum Route Saved as "+routes_file)
