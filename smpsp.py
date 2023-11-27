# Author: Lennon Conson
# TODO Need to switch all of the input files to square meters

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory
import os
import tracemalloc
import csv
from datetime import date
from datetime import timedelta

tracemalloc.start()

model = ConcreteModel('Stochastic Military Port Selection Problem')

# Importing packages.csv file
def process_packages_csv(file_path='packages.csv'):
    packages_dict = {}
    with open(file_path, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            new_row = row.copy()
            package_id = row['Package ID']
            del new_row['Package ID']
            packages_dict[package_id] = new_row
            packages_dict[package_id]['RLD'] = date.fromisoformat(packages_dict[package_id]['RLD'])
            packages_dict[package_id]['EAD'] = date.fromisoformat(packages_dict[package_id]['EAD'])
            packages_dict[package_id]['LAD'] = date.fromisoformat(packages_dict[package_id]['LAD'])
            packages_dict[package_id]['Ordinal RLD'] = None
            packages_dict[package_id]['Ordinal EAD'] = None
            packages_dict[package_id]['Ordinal LAD'] = None
            packages_dict[package_id]['Square Meters'] = float(packages_dict[package_id]['Square Meters'])
    return packages_dict

# To use the function and get the dictionary:
P = process_packages_csv()


# Set of Origins
I = set()

#Set of Destinations
K = set()

# Iterate through all keys in the dictionary and add their values to the origin/detination set

#TODO there is a more eligant method that escapes me right now.
latestDate = date(2025, 12, 3)
earliestDate = date(2324, 4, 24)

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
    indexDate += timedelta(days=1)

# TODO Add the ordinal date.

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

# Load in Daily Port Processing Limits
b = {}

port_limits_file = "daily-port-processing-capabilities.csv"
# Encoded Packages Dictionary with Packages CSV file
with open(port_limits_file, mode='r') as file:
    csv_reader = csv.reader(file)
    
    next(csv_reader)
    
    for row in csv_reader:
        key = row[0]
        value = float(row[1])
        b[key] = value

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
    return sum(((t - earliestDate).days + c[P[p]['Origin'],j ]) * model.x[p,j,t] for p in P.keys() for j in J for t in T)

model.obj = pyo.Objective(rule=obj_rule)

# Constraints

# Ensure a package only goes through a single port
def singlePort(model, p):
    return sum(model.x[p, j, t] for j in J for t in T) == 1

model.constSinglePort = Constraint(P.keys(), rule=singlePort)

print("Dimension of Single Port Constraint is " + str(len(model.constSinglePort)))

# Ensure a package doesn't leave origin before the RLD
def rld(model,p):
    indexDate = earliestDate

    eldDates = [indexDate]
    indexDate += timedelta(days=1)
    
    lastDate = P[p]['RLD']

    while indexDate < lastDate:
        eldDates.append(indexDate)
        indexDate += timedelta(days=1)

    return sum(model.x[p,j,t] for j in J for t in eldDates) == 0

model.constRLD = Constraint(P.keys(), rule=rld)

# Ensure a SPOE does not exceed daily processing.
def capSPOE(model,j,t):
    return sum(P[p]['Square Meters']*(model.x[p,j,t]) for p in P.keys()) <= b[j]

model.constCapSPOE = Constraint(J, T, rule=capSPOE)


print("Dimension of RLD Constraint is " + str(len(model.constRLD)))

opt = pyo.SolverFactory('cplex') 
results = opt.solve(model)
pyo.assert_optimal_termination(results)
# model.display()

# print("Optimal solution found with objective value:", model.obj())

# Routes Output Routine
routes = []

for p in P.keys():
    for j in J:
        for t in T:
            i = P[p]['Origin']
            RLD = P[p]['RLD']
            if model.x[p, j, t].value == 1:
                routes.append((p,i, RLD, t, j, c[(i,j)]))

routes_file = 'routes.csv'
with open(routes_file, 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(['Package ID', 'Origin', 'RLD', 'Depart Origin','SPOE','Travel Time to SPOE'])
    csv_writer.writerows(routes)
print("Optimum Route Saved as "+routes_file)

# SPOE Daily Incoming Usage
spoe_daily = {}

for j in J:
    for t in T:
        cap = 0
        for p in P.keys():
            cap += P[p]['Square Meters']*model.x[p,j,t]()
        spoe_daily[(j,t)] = cap

daily_spoe_inflow = "daily_spoe_inflow.csv"

with open(daily_spoe_inflow, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['SPOE', 'Date', 'Inflow','Capacity'])
    for (j, t), cap in spoe_daily.items():
        csvwriter.writerow([j, t, cap, b[j]])
print("Daily SPOE Inflow Processing  as "+ daily_spoe_inflow)

