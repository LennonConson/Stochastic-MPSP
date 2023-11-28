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
            #Convert Strings to Dates
            packages_dict[package_id]['RLD'] = date.fromisoformat(packages_dict[package_id]['RLD'])
            packages_dict[package_id]['EAD'] = date.fromisoformat(packages_dict[package_id]['EAD'])
            packages_dict[package_id]['LAD'] = date.fromisoformat(packages_dict[package_id]['LAD'])
            # Add Place holder for Ordinal Date
            packages_dict[package_id]['Ordinal RLD'] = None
            packages_dict[package_id]['Ordinal EAD'] = None
            packages_dict[package_id]['Ordinal LAD'] = None
            #Convert String to a Floats
            packages_dict[package_id]['Square Meters'] = float(packages_dict[package_id]['Square Meters'])
    return packages_dict

# To use the function and get the dictionary:
package_dict = process_packages_csv()

# Set up Origins, SPODs, and find the time horizon
origins = set()
spods = set()

#TODO there is a more eligant method that escapes me right now.
latest_date = date(1900, 12, 3)
earliest_date = date(2324, 4, 24)

for key in package_dict:
    origins.add(package_dict[key]['Origin'])
    spods.add(package_dict[key]['SPOD'])
    if package_dict[key]['RLD'] < earliest_date:
        earliest_date = package_dict[key]['RLD']
    if package_dict[key]['LAD'] > latest_date:
        latest_date = package_dict[key]['LAD']

# Find the Ordinal RLD, EAD, LAD
for key in package_dict:
    package_dict[key]['Ordinal RLD'] = (package_dict[key]['RLD'] - earliest_date).days
    package_dict[key]['Ordinal RLD'] = (package_dict[key]['RLD'] - earliest_date).days
    package_dict[key]['Ordinal RLD'] = (package_dict[key]['RLD'] - earliest_date).days



time_horizon = range((latest_date-earliest_date).days)

# Setup intracontential travel time durations and set of spoes
intra_duration = {}
spoes = set()

with open('intracontinental.times.csv') as csv_file:
    reader = csv.reader(csv_file)
    next(reader)
    for row in reader:
        key = (row[0], row[1])
        value = float(row[2])
        intra_duration[key] = value
        spoes.add(row[1])

# Load in Daily Port Processing Limits
daily_processing_limits = {}

port_limits_file = "daily-port-processing-capabilities.csv"

# Encoded Packages Dictionary with Packages CSV file
with open("daily-port-processing-capabilities.csv") as csv_file:
    reader = csv.reader(csv_file)
    next(reader)
    for row in reader:
        key = row[0]
        value = float(row[1])
        daily_processing_limits[key] = value

print("Check to make sure there are no slight variations of spelling in list of Origins.")
print("")
print("Origins")
print("-------------------")
for i in origins:
    print(i)

print("Check to make sure there are no slight variations of spelling in list of SPOE.")
print("")
print("SPOE")
print("-------------------")
for j in spoes:
    print(j)

print("Check to make sure there are no slight variations of spelling in list of SPOD.")
print("")
print("SPOD")
print("-------------------")
for k in spods:
    print(k)



# Decision Variables
model.x = Var(package_dict.keys(), spoes, time_horizon, domain=Binary)

print("")
print("Dimension of x_pjt is " + str(len(model.x)))

# Objective
# TODO Current Objective not very useful
def obj_rule(model):
    return sum((t + intra_duration[package_dict[p]['Origin'],j ]) * model.x[p,j,t] for p in package_dict.keys() for j in spoes for t in time_horizon)

model.obj = pyo.Objective(rule=obj_rule)

# Constraints
# Ensure a package only goes through a single port
def single_port(model, p):
    return sum(model.x[p, j, t] for j in spoes for t in time_horizon) == 1

model.constSinglePort = Constraint(package_dict.keys(), rule=single_port)

print("Dimension of Single Port Constraint is " + str(len(model.constSinglePort)))

quit()
# Ensure a package doesn't leave origin before the RLD
def rld(model,p):
    indexDate = earliest_date

    eldDates = [indexDate]
    indexDate += timedelta(days=1)
    
    lastDate = P[p]['RLD']

    while indexDate < lastDate:
        eldDates.append(indexDate)
        indexDate += timedelta(days=1)

    return sum(model.x[p,j,t] for j in J for t in eldDates) == 0

model.constRLD = Constraint(P.keys(), rule=rld)
quit()
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

