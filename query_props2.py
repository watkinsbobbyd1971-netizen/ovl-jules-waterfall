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

with open('filtered_wd_map.json') as f:
    wd_map = json.load(f)

wd_ids = list(set(wd_map.values()))
all_results = {}

print(f"Total unique WD IDs to query: {len(wd_ids)}")

def query_batch(ids):
    values = " ".join([f'wd:{i}' for i in ids])
    query = f"""
    SELECT ?item ?prop ?psn_val ?valLabel WHERE {{
      VALUES ?item {{ {values} }}
      VALUES ?prop {{ wd:P527 wd:P31 wd:P279 wd:P2043 wd:P170 wd:P176 wd:P2067 wd:P186 wd:P2102 wd:P2874 }}

      ?prop wikibase:claim ?p_uri.
      ?prop wikibase:statementProperty ?ps.

      ?item ?p_uri ?statement.
      ?statement ?ps ?val.

      OPTIONAL {{
        ?prop wikibase:statementValueNormalized ?psn .
        ?statement ?psn ?val_norm .
        ?val_norm wikibase:quantityAmount ?psn_val .
      }}

      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """

    url = 'https://query.wikidata.org/sparql'
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'query': query}).encode(), headers={'User-Agent': 'MyBot_9a8b7c6d/1.0', 'Accept': 'application/sparql-results+json'})

    retries = 3
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
                data = json.loads(response.read().decode())
                return data['results']['bindings']
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)
    return []

for i in range(0, len(wd_ids), 50):
    chunk = wd_ids[i:i+50]
    bindings = query_batch(chunk)
    for b in bindings:
        item = b['item']['value'].split('/')[-1]
        p = b['prop']['value'].split('/')[-1]

        if 'psn_val' in b:
            val = b['psn_val']['value']
        else:
            val = b['valLabel']['value']

        if item not in all_results:
            all_results[item] = {}
        if p not in all_results[item]:
            all_results[item][p] = []
        all_results[item][p].append(val)

    time.sleep(0.5)

print(f"Got properties for {len(all_results)} items")
with open('wd_props.json', 'w') as f:
    json.dump(all_results, f)
