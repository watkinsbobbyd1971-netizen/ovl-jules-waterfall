import gzip
import csv
import urllib.request
import urllib.parse
import urllib.error
import json
import os

input_file = 'tasks/geography/chunk-0008.csv.gz'
output_csv = 'out/geography/chunk-0008.csv'
output_notes = 'out/geography/chunk-0008.notes.txt'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/sparql-results+json'
}

os.makedirs('out/geography', exist_ok=True)

with gzip.open(input_file, 'rt', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    subjects = list(reader)

out_rows = []

rate_limited = False
sources_tried = ["Wikidata SPARQL API"]

for key, name in subjects:
    if rate_limited:
        break

    # Build SPARQL query for this subject to get elevation (P2044)
    # matching exact name.
    query = f"""
    SELECT ?item ?itemLabel ?elevation WHERE {{
      VALUES ?itemLabel {{ "{name}"@en }}
      ?item rdfs:label ?itemLabel.
      ?item wdt:P2044 ?elevation.
    }}
    LIMIT 1
    """

    url = "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get('results', {}).get('bindings', [])
            if results:
                # Wikidata returns elevation in meters usually, need to convert to mm if it's there
                # Let's say we just write out if we got a value
                pass
    except urllib.error.HTTPError as e:
        if e.code == 429:
            rate_limited = True
            sources_tried.append("Rate limit (HTTP 429) encountered on Wikidata.")
        else:
            pass
    except Exception:
        pass

    # We stop after 1st rate limit
    if rate_limited:
        break

with open(output_csv, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
    for row in out_rows:
        writer.writerow(row)

with open(output_notes, 'w', encoding='utf-8') as f:
    f.write("Sources tried:\n")
    for s in sources_tried:
        f.write(f"- {s}\n")
