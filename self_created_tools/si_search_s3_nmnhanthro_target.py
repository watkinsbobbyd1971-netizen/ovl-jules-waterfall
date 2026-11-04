import urllib.request
import json
import gzip
import csv
import sys
import os
import random

targets = set()
with gzip.open("tasks/cultural_object/chunk-0004.csv.gz", "rt", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        targets.add(row[0].strip())

print(f"Total targets: {len(targets)}")

# Is there any other way to map SMI identifiers?
# Wait! "0475223" - in EDAN, the "id" is usually things like "edanmdm-nmnhanthro_8475223" or similar.
# The keys in the task are "LIBSRC-LIB51-ENT-SMI-0475223".
# Is there a dataset on the system that maps these?
