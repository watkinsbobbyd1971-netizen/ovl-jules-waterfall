import urllib.request
import urllib.parse
import json
import gzip
import os
import csv

# Load targets
targets = set()
with gzip.open("tasks/cultural_object/chunk-0004.csv.gz", "rt", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        # the key is like LIBSRC-LIB51-ENT-SMI-0475223
        # extract the number
        number = row[0].split('-')[-1]
        targets.add(number)

print(f"Loaded {len(targets)} targets")

url = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/index.txt"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    content = response.read().decode('utf-8')
    indexes = [line.strip() for line in content.split('\n') if line.strip()]

found_count = 0
# Let's search a few indexes and see if any have "475223"
for idx_group in indexes:
    if found_count > 0:
        break
    if "nmah" not in idx_group and "chndm" not in idx_group and "nmnh" not in idx_group:
        # Just skip for now to save time, let's search NMAH, CHNDM, NMNH
        continue

    print(f"Searching {idx_group}")
    req = urllib.request.Request(idx_group)
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            sub_indexes = [line.strip() for line in content.split('\n') if line.strip()]
            for sub_idx in sub_indexes[:1]: # just first file
                req2 = urllib.request.Request(sub_idx)
                with urllib.request.urlopen(req2) as resp2:
                    for line in resp2:
                        line = line.decode('utf-8')
                        if any(t in line for t in list(targets)[:50]):
                            print(f"Found something in {sub_idx}")
                            found_count += 1
                            break
    except Exception as e:
        print(e)
