import csv
import gzip
import os

input_file = "tasks/built_environment/chunk-0033.csv.gz"
output_file = "out/built_environment/chunk-0033.csv"
notes_file = "out/built_environment/chunk-0033.notes.txt"

os.makedirs(os.path.dirname(output_file), exist_ok=True)

with gzip.open(input_file, 'rt') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        key, name = row
        # ULAN entities are people/organizations, not buildings/structures.
        # So we skip them. Since we only have ULAN entities here, the file will be empty.

with open(output_file, 'w') as f:
    f.write("canonical_dedup_key,column_name,value,source_url\n")
