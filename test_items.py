import gzip
import csv

with gzip.open('tasks/plant/chunk-0000.csv.gz', 'rt') as f:
    reader = csv.DictReader(f)
    items = [row['subject_name'] for row in reader]

print(f"Total items: {len(items)}")
print(f"Sample items: {items[:20]}")
