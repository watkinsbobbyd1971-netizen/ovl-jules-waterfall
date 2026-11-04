import gzip
import csv

input_file = "tasks/historical_protective/chunk-0006.csv.gz"

with gzip.open(input_file, "rt") as f:
    reader = csv.reader(f)
    header = next(reader)
    for i, row in enumerate(reader):
        print(row)
        if i >= 10:
            break
