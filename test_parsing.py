import json

data = [
    {"scientificName": "Navicula crassula Naegeli, 1849", "canonicalName": "Navicula crassula"},
    {"scientificName": "Navicula siberica Skvortzow, 1929", "canonicalName": "Navicula siberica"},
    {"scientificName": "Coccomyces castanopsidis (Seaver) Sherwood", "canonicalName": "Coccomyces castanopsidis"},
    {"scientificName": "Coccomyces proteae Marinc., M.J.Wingf. & Crous", "canonicalName": "Coccomyces proteae"},
]

for d in data:
    sci = d['canonicalName']
    auth = d['scientificName'].replace(d['canonicalName'], "").strip()
    print(f"Scientific: {sci} | Authority: {auth}")
