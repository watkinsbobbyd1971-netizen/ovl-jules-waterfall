import urllib.request
import urllib.parse
import json
import time
import gzip
import csv
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

subjects = []
with gzip.open('tasks/machinery/chunk-0022.csv.gz', 'rt') as f:
    reader = csv.DictReader(f)
    for row in reader:
        subjects.append(row)

# Batch search all labels
def search_sparql_labels(labels):
    values = " ".join([f'"{l.replace("\"", "")}"@en' for l in labels])
    query = f"""
    SELECT ?item ?itemLabel ?desc WHERE {{
      VALUES ?itemLabel {{ {values} }}
      ?item rdfs:label ?itemLabel.
      OPTIONAL {{ ?item schema:description ?desc . FILTER(LANG(?desc) = "en") }}
    }}
    """
    url = 'https://query.wikidata.org/sparql'
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'query': query}).encode(), headers={'User-Agent': 'MyBot_9a8b7c6d/1.0', 'Accept': 'application/sparql-results+json'})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            data = json.loads(response.read().decode())
            res = {}
            for item in data['results']['bindings']:
                label = item['itemLabel']['value']
                wd_id = item['item']['value'].split('/')[-1]
                desc = item.get('desc', {}).get('value', '').lower()
                if label not in res:
                    res[label] = []
                res[label].append({'id': wd_id, 'desc': desc})
            return res
    except Exception as e:
        print(f"Error: {e}")
        return {}

# Memory says:
# "When querying Wikidata for subjects formatted as 'Last, First' (e.g., artists with ULAN IDs), parsing and reversing the string to 'First Last' before querying wbsearchentities significantly improves exact match rates."
# We'll just search direct match.

results_map = {}
labels = [s['subject_name'] for s in subjects]
for i in range(0, len(labels), 50):
    chunk = labels[i:i+50]
    res = search_sparql_labels(chunk)
    results_map.update(res)
    time.sleep(1)

print(f"Found matches for {len(results_map)} labels out of {len(labels)}")
with open('wd_map.json', 'w') as f:
    json.dump(results_map, f)
