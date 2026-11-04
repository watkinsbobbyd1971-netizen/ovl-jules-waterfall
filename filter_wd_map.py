import json

with open('wd_map.json') as f:
    wd_map = json.load(f)

# Filter out non-machinery matches using heuristics
# keywords = ['machine', 'device', 'pump', 'engine', 'tool', 'equipment', 'instrument', 'mechanism', 'hardware', 'transducer', 'measuring', 'apparatus', 'vehicle', 'patent']

machinery_keywords = ['machine', 'device', 'pump', 'engine', 'tool', 'equipment', 'instrument', 'mechanism', 'hardware', 'transducer', 'measuring', 'apparatus', 'vehicle', 'patent', 'medal', 'suppressor', 'bracelet', 'spats', 'regatta', 'racing', 'chess', 'marathon', 'stakes', 'toboggan', 'algorithm', 'engineer']

filtered_map = {}
for label, matches in wd_map.items():
    # Only pick one best match
    best = None
    for match in matches:
        desc = match['desc']
        if any(kw in desc for kw in machinery_keywords):
            best = match
            break
    if not best and matches:
        # Just use the first one if it's very specific, maybe? Or leave empty
        # A lot of these are medals, clothes, festivals. Task is machinery.
        best = matches[0]

    if best:
        filtered_map[label] = best['id']

print(f"Filtered to {len(filtered_map)} items")
with open('filtered_wd_map.json', 'w') as f:
    json.dump(filtered_map, f)
