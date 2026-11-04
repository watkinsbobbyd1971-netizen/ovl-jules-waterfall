import csv
import gzip
import json
import urllib.request
import urllib.parse
import os
import concurrent.futures

category = "invertebrate"
chunk = "0003"
input_file = f"tasks/{category}/chunk-{chunk}.csv.gz"
output_dir = f"out/{category}"
output_file = f"{output_dir}/chunk-{chunk}.csv"
notes_file = f"{output_dir}/chunk-{chunk}.notes.txt"

os.makedirs(output_dir, exist_ok=True)

with gzip.open(input_file, "rt") as f:
    rows = list(csv.DictReader(f))

def fetch_gbif(row):
    key = row["canonical_dedup_key"]
    subject_name = row["subject_name"]
    gbif_url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(subject_name)}"

    local_results = []

    try:
        req = urllib.request.Request(gbif_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())

            if data.get("matchType") == "EXACT":
                if "scientificName" in data:
                    local_results.append({
                        "canonical_dedup_key": key,
                        "column_name": "scientific_identity",
                        "value": json.dumps(data["scientificName"]),
                        "source_url": gbif_url
                    })
                author = data.get("scientificName", "").replace(data.get("canonicalName", ""), "").strip()
                if not author and "authorship" in data:
                    author = data["authorship"]
                if author:
                    local_results.append({
                        "canonical_dedup_key": key,
                        "column_name": "taxon_authority",
                        "value": json.dumps(author),
                        "source_url": gbif_url
                    })
    except Exception as e:
        pass

    return local_results

results = []
tried_sources = {"GBIF API (species/match)"}

print(f"Starting threads for {len(rows)} rows...")
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    for res in executor.map(fetch_gbif, rows):
        results.extend(res)

print("Writing output...")
with open(output_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["canonical_dedup_key", "column_name", "value", "source_url"])
    for r in results:
        writer.writerow([r["canonical_dedup_key"], r["column_name"], r["value"], r["source_url"]])

with open(notes_file, "w") as f:
    f.write(f"Tried sources:\n")
    for s in tried_sources:
        f.write(f"- {s}\n")

print(f"Done. Wrote {len(results)} rows to {output_file}")
