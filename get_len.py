import csv
import gzip

category = "invertebrate"
chunk = "0003"
input_file = f"tasks/{category}/chunk-{chunk}.csv.gz"

with gzip.open(input_file, "rt") as f:
    reader = list(csv.DictReader(f))
    print(f"Total rows: {len(reader)}")
