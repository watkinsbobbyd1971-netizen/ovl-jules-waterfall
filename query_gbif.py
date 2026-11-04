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

with gzip.open(input_file, "rt") as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = row["canonical_dedup_key"]
        subject_name = row["subject_name"]

        # Try GBIF
        gbif_url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(subject_name)}"
        tried_sources.add("GBIF API (species/match)")

        try:
            req = urllib.request.Request(gbif_url)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())

                if data.get("matchType") == "EXACT":
                    if "scientificName" in data:
                        results.append({
                            "canonical_dedup_key": key,
                            "column_name": "scientific_identity",
                            "value": json.dumps(data["scientificName"]),
                            "source_url": gbif_url
                        })
                    if "authorship" in data:
                        results.append({
                            "canonical_dedup_key": key,
                            "column_name": "taxon_authority",
                            "value": json.dumps(data["authorship"]),
                            "source_url": gbif_url
                        })
                    elif data.get("scientificName", "").replace(data.get("canonicalName", ""), "").strip():
                         author = data.get("scientificName", "").replace(data.get("canonicalName", ""), "").strip()
                         if author:
                             results.append({
                                 "canonical_dedup_key": key,
                                 "column_name": "taxon_authority",
                                 "value": json.dumps(author),
                                 "source_url": gbif_url
                             })
        except Exception as e:
            print(f"Error querying GBIF for {subject_name}: {e}")
            pass

        # Try Wikidata
        query = """
        SELECT ?item ?itemLabel ?taxonName ?taxonAuthorLabel WHERE {
          ?item wdt:P225 "%s".
          ?item wdt:P225 ?taxonName.
          OPTIONAL { ?item wdt:P405 ?taxonAuthor. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        """ % subject_name

        wikidata_url = f"https://query.wikidata.org/sparql?query={urllib.parse.quote(query)}&format=json"
        tried_sources.add("Wikidata SPARQL (taxon name, P225, P405)")

        try:
            req = urllib.request.Request(wikidata_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())

                bindings = data.get("results", {}).get("bindings", [])
                if len(bindings) == 1: # Strict match, skip ambiguous
                    b = bindings[0]
                    item_url = b.get("item", {}).get("value")
                    if "taxonName" in b:
                        results.append({
                            "canonical_dedup_key": key,
                            "column_name": "scientific_identity",
                            "value": json.dumps(b["taxonName"]["value"]),
                            "source_url": item_url
                        })
                    if "taxonAuthorLabel" in b:
                        results.append({
                            "canonical_dedup_key": key,
                            "column_name": "taxon_authority",
                            "value": json.dumps(b["taxonAuthorLabel"]["value"]),
                            "source_url": item_url
                        })
        except Exception as e:
            print(f"Error querying Wikidata for {subject_name}: {e}")
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
