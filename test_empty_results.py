import csv

with open('out/invertebrate/chunk-0008.csv', 'r') as f:
    reader = csv.DictReader(f)
    keys = set()
    for row in reader:
        keys.add(row['canonical_dedup_key'])

print(f"Number of subjects with at least one filled property: {len(keys)}")
