import csv
from datetime import date

P = {}
with open('packages.csv', newline='') as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        new_row = row.copy()
        PackageID = row['Package ID']
        del new_row['Package ID']
        P[PackageID] = new_row
        P[PackageID]['RLD'] = date.fromisoformat(P[PackageID]['RLD'])
        P[PackageID]['EAD'] = date.fromisoformat(P[PackageID]['EAD'])
        P[PackageID]['LAD'] = date.fromisoformat(P[PackageID]['LAD'])
        P[PackageID]['nominalRLD'] = None
        P[PackageID]['nominalEAD'] = None
        P[PackageID]['nominalLAD'] = None

