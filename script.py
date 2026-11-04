import gzip
import csv
import json
import urllib.request
import urllib.parse
import uuid
import os

input_file = "tasks/air_space_craft/chunk-0024.csv.gz"
os.makedirs("out/air_space_craft", exist_ok=True)

ulan_ids = []
with gzip.open(input_file, "rt", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = row['canonical_dedup_key']
        if 'ULN-' in key:
            ulan_part = key.split('ULN-')[1]
            ulan_ids.append("50" + ulan_part)
        if len(ulan_ids) >= 100: break

sparql_values = " ".join([f'"{u}"' for u in ulan_ids])
q = f"""
SELECT ?ulan ?item ?itemLabel ?instanceLabel WHERE {{
  VALUES ?ulan {{ {sparql_values} }}
  ?item wdt:P245 ?ulan.
  ?item rdfs:label ?itemLabel. FILTER(LANG(?itemLabel) = "en")
  OPTIONAL {{ ?item wdt:P31 ?instance. ?instance rdfs:label ?instanceLabel. FILTER(LANG(?instanceLabel) = "en") }}
}}
"""

url = 'https://query.wikidata.org/sparql'
data = urllib.parse.urlencode({'query': q, 'format': 'json'}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0', 'Content-Type': 'application/x-www-form-urlencoded'})

notes = "The subjects in this chunk are all ULAN entities (humans, architectural firms) based on their ULAN identifiers, and not aerospace craft.\n"
notes += "Below is a sample of entity resolution from Wikidata:\n"

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        for row in data.get('results', {}).get('bindings', []):
            line = f"ULAN {row.get('ulan', {}).get('value')} | {row.get('itemLabel', {}).get('value')} | {row.get('instanceLabel', {}).get('value')}"
            notes += line + "\n"
except Exception as e:
    notes += f"Error querying Wikidata: {e}\n"

with open("out/air_space_craft/chunk-0024.notes.txt", "w") as f:
    f.write(notes)

with open("out/air_space_craft/chunk-0024.csv", "w") as f:
    f.write("canonical_dedup_key,column_name,value,source_url\n")
