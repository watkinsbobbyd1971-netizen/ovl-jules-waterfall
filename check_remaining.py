import gzip
import csv
import os

in_file = "tasks/built_environment/chunk-0079.csv.gz"
out_file = "out/built_environment/chunk-0079.csv"

with gzip.open(in_file, 'rt') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

processed_keys = set()
if os.path.exists(out_file):
    with open(out_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            processed_keys.add(row['canonical_dedup_key'])

print(f"Total keys in tasks: {len(set(r['canonical_dedup_key'] for r in rows))}")
print(f"Keys processed (found data): {len(processed_keys)}")
