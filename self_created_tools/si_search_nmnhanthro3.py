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

print(f"Loaded {len(targets)} targets")

url = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/nmnhanthro/00.txt"
req = urllib.request.Request(url)
found = 0
try:
    with urllib.request.urlopen(req) as response:
        for line in response:
            line_str = line.decode('utf-8')
            for t in list(targets)[:200]:
                if f'"record_ID":"nmnhanthro_{t}"' in line_str or f'"record_ID":"nmnhanthro_1{t}"' in line_str or f'"record_ID":"nmnhanthro_8{t}"' in line_str:
                    print(f"Found target {t}!")
                    data = json.loads(line_str)
                    print(json.dumps(data, indent=2)[:500])
                    found += 1
                    break
            if found >= 2:
                break
except Exception as e:
    print(e)
