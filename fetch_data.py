import csv
import gzip
import json
import urllib.request
import urllib.parse
import concurrent.futures
import os
import time

os.makedirs("out/invertebrate", exist_ok=True)

def process_subject(row):
    key = row["canonical_dedup_key"]
    name = row["subject_name"]
    results = []
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(name)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get("matchType") == "EXACT" and data.get("canonicalName"):
                results.append((key, "scientific_identity", data["canonicalName"], url))
                scientific_name = data.get("scientificName", "")
                if scientific_name.startswith(data["canonicalName"]):
                    authority = scientific_name[len(data["canonicalName"]):].strip()
                    if authority:
                        results.append((key, "taxon_authority", authority, url))
    except Exception as e:
        pass
    return results

in_file = "tasks/invertebrate/chunk-0077.csv.gz"
out_file = "out/invertebrate/chunk-0077.csv"

with gzip.open(in_file, "rt") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    all_results = list(executor.map(process_subject, rows))

with open(out_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["canonical_dedup_key", "column_name", "value", "source_url"])
    for results in all_results:
        writer.writerows(results)
