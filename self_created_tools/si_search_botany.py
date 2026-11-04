
import urllib.request
import json
import gzip
import csv

targets = set()
with gzip.open("tasks/cultural_object/chunk-0004.csv.gz", "rt", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        number = row[0].split("-")[-1]
        targets.add(number)

url = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/nmnhbotany/00.txt"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    for line in response:
        line_str = line.decode("utf-8")
        if "0489809" in line_str:
            data = json.loads(line_str)
            print(json.dumps(data, indent=2))
            break
