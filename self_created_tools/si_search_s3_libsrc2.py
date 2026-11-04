import urllib.request
import urllib.parse
import json
import gzip
import os
import csv
import io

# Load targets
targets = set()
with gzip.open("tasks/cultural_object/chunk-0004.csv.gz", "rt", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        targets.add(row[0].strip())

print(f"Loaded {len(targets)} targets")

url = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/si/index.txt"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    content = response.read().decode('utf-8')
    indexes = [line.strip() for line in content.split('\n') if line.strip()]

print(f"SI index files: {len(indexes)}")
if indexes:
    req = urllib.request.Request(indexes[0])
    with urllib.request.urlopen(req) as response:
        for line in response:
            try:
                data = json.loads(line)
                if "id" in data:
                    pass
            except Exception as e:
                pass
