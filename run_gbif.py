import csv
import gzip
import json
import urllib.request
import urllib.parse
import os

category = "invertebrate"
chunk = "0003"
input_file = f"tasks/{category}/chunk-{chunk}.csv.gz"
output_dir = f"out/{category}"
output_file = f"{output_dir}/chunk-{chunk}.csv"
notes_file = f"{output_dir}/chunk-{chunk}.notes.txt"

os.makedirs(output_dir, exist_ok=True)

results = []
tried_sources = set()

# deduplicate (key, column_name) to keep the first one
seen = set()

with gzip.open(input_file, "rt") as f:
    reader = list(csv.DictReader(f))

print(f"Loaded {len(reader)} rows.")

for i, row in enumerate(reader):
    key = row["canonical_dedup_key"]
    subject_name = row["subject_name"]

    if i % 10 == 0:
        print(f"Processing row {i} / {len(reader)}")

    # Try GBIF
    gbif_url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(subject_name)}"
    tried_sources.add("GBIF API (species/match)")

    try:
        req = urllib.request.Request(gbif_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())

            if data.get("matchType") == "EXACT":
                if "scientificName" in data:
                    if (key, "scientific_identity") not in seen:
                        results.append({
                            "canonical_dedup_key": key,
                            "column_name": "scientific_identity",
                            "value": json.dumps(data["scientificName"]),
                            "source_url": gbif_url
                        })
                        seen.add((key, "scientific_identity"))
                author = data.get("scientificName", "").replace(data.get("canonicalName", ""), "").strip()
                if not author and "authorship" in data:
                    author = data["authorship"]
                if author:
                    if (key, "taxon_authority") not in seen:
                        results.append({
                            "canonical_dedup_key": key,
                            "column_name": "taxon_authority",
                            "value": json.dumps(author),
                            "source_url": gbif_url
                        })
                        seen.add((key, "taxon_authority"))
    except Exception as e:
        print(f"Error querying GBIF for {subject_name}: {e}")
        pass

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
