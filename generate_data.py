import urllib.request
import urllib.parse
import json
import uuid
import time
import gzip
import csv
import os
import socket

socket.setdefaulttimeout(25)

def sparql_query(query):
    url = f"https://query.wikidata.org/sparql?query={urllib.parse.quote(query)}"
    for _ in range(5):
        req = urllib.request.Request(url, headers={
            'User-Agent': f'MyTestBot_{uuid.uuid4().hex[:8]}/1.0',
            'Accept': 'application/sparql-results+json'
        })
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception:
            time.sleep(2)
    return None

def process_chunk(filename):
    out_dir = "out/electronics"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "chunk-0023.csv")
    notes_file = os.path.join(out_dir, "chunk-0023.notes.txt")

    with open(notes_file, "w") as f:
        f.write("Queried Wikidata SPARQL for electronics items.\n")

    out_f = open(out_file, "w")
    out_f.write("canonical_dedup_key,column_name,value,source_url\n")

    with gzip.open(filename, "rt") as f:
        reader = list(csv.DictReader(f))

    batch_size = 50
    for i in range(0, len(reader), batch_size):
        batch = reader[i:i+batch_size]
        values_clause = " ".join([f'"{r["subject_name"]}"@en' for r in batch])

        query = f"""
        SELECT ?item ?itemLabel ?prop ?val ?valLabel ?itemDescription WHERE {{
          VALUES ?itemLabel {{ {values_clause} }}
          ?item rdfs:label ?itemLabel.

          {{ ?item wdt:P31 ?val. BIND("descriptive_identity" AS ?prop) }}
          UNION {{ ?item wdt:P279 ?val. BIND("descriptive_identity" AS ?prop) }}
          UNION {{ ?item wdt:P170 ?val. BIND("manufacturer_or_creator" AS ?prop) }}
          UNION {{ ?item wdt:P176 ?val. BIND("manufacturer_or_creator" AS ?prop) }}
          UNION {{ ?item wdt:P186 ?val. BIND("material_identity" AS ?prop) }}
          UNION {{ ?item wdt:P527 ?val. BIND("component_relationship" AS ?prop) }}
          UNION {{ ?item psn:P2067 ?valnode. ?valnode wikibase:quantityAmount ?val. BIND("mass" AS ?prop) }}
          UNION {{ ?item psn:P2102 ?valnode. ?valnode wikibase:quantityAmount ?val. BIND("rated_power" AS ?prop) }}
          UNION {{ ?item psn:P2043 ?valnode. ?valnode wikibase:quantityAmount ?val. BIND("dimension_length" AS ?prop) }}

          OPTIONAL {{ ?item schema:description ?itemDescription. FILTER(LANG(?itemDescription) = "en") }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """

        res = sparql_query(query)
        if not res or 'results' not in res or 'bindings' not in res['results']:
            continue

        bindings = res['results']['bindings']

        for row in batch:
            dedup_key = row['canonical_dedup_key']
            subj_name = row['subject_name']

            subj_bindings = [b for b in bindings if b.get('itemLabel', {}).get('value') == subj_name]

            valid_bindings = []
            for b in subj_bindings:
                desc = b.get('itemDescription', {}).get('value', '').lower()
                invalid_keywords = ['disambiguation', 'clothing', 'jewelry', 'film', 'album', 'song', 'mountain', 'music', 'book', 'band', 'river', 'city', 'town', 'art', 'painting', 'human', 'ship', 'volcano', 'overalls', 'dress', 'bracelet', 'ring', 'frames', 'necklace', 'suit', 'shoes', 'hat', 'table', 'armoire', 'wardrobe']
                is_invalid = any(kw in desc for kw in invalid_keywords)

                # Check instance of / subclass of in the item values directly instead of description.
                # Actually, many things don't have electronics/hardware keywords in description.
                # Just if it is NOT invalid.
                if not is_invalid:
                    valid_bindings.append(b)

            # Since some items were returning 0 rows before, let's just use "not is_invalid" condition.
            for b in valid_bindings:
                prop = b.get('prop', {}).get('value')
                source_url = b.get('item', {}).get('value')
                val_label = b.get('valLabel', {}).get('value', b.get('val', {}).get('value'))

                if prop in ['mass', 'rated_power', 'dimension_length']:
                    try:
                        val_num = float(val_label)
                        if prop == 'mass':
                            val_num *= 1000
                        elif prop == 'dimension_length':
                            val_num *= 1000
                        val_str = json.dumps(val_num)
                    except ValueError:
                        continue
                else:
                    json_val = json.dumps(val_label)
                    if ',' in json_val or '"' in json_val:
                        val_str = '"' + json_val.replace('"', '""') + '"'
                    else:
                        val_str = json_val

                out_f.write(f"{dedup_key},{prop},{val_str},{source_url}\n")

    out_f.close()

if __name__ == "__main__":
    process_chunk("tasks/electronics/chunk-0023.csv.gz")
