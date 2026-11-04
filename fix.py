import csv
import json

with open("out/household/chunk-0025.csv", "r") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("Actual CSV representation of first row:")
print(repr(rows[0]['value']))
