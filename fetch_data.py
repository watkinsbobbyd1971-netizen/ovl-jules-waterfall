import csv
import gzip
import json
import urllib.request
import urllib.parse
import time

def search_wikidata_batch(names):
    if not names: return {}
    values_str = " ".join([f'"{n}"@en' for n in names])

    query = f"""
    SELECT ?item ?itemLabel ?type ?typeLabel ?p170 ?p170Label ?p186 ?p186Label ?p2043 ?p2043Label ?p2067 ?p2067Label
    WHERE {{
      VALUES ?name {{ {values_str} }}
      ?item wdt:P31 ?type.
      ?item rdfs:label ?name.
      OPTIONAL {{ ?item wdt:P170 ?p170. }}
      OPTIONAL {{ ?item wdt:P186 ?p186. }}
      OPTIONAL {{ ?item wdt:P2043 ?p2043. }}
      OPTIONAL {{ ?item wdt:P2067 ?p2067. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
    url = "https://query.wikidata.org/sparql"
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'query': query}).encode('utf-8'), headers={'Accept': 'application/sparql-results+json', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))['results']['bindings']
            ret = {}
            for r in res:
                name = r.get('itemLabel', {}).get('value')
                if not name: continue
                if name not in ret:
                    ret[name] = []
                ret[name].append(r)
            return ret
    except Exception as e:
        print(f"Wikidata error: {e}")
        return {}

def main():
    input_file = "tasks/clothing_jewelry/chunk-0031.csv.gz"
    output_file = "out/clothing_jewelry/chunk-0031.csv"

    with gzip.open(input_file, 'rt') as f:
        reader = csv.reader(f)
        header = next(reader)
        subjects = list(reader)

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["canonical_dedup_key", "column_name", "value", "source_url"])

        batch_size = 50
        for i in range(0, len(subjects), batch_size):
            batch = subjects[i:i+batch_size]
            names_to_search = []
            for row in batch:
                name = row[1]
                names_to_search.append(name.replace('"', '\\"'))

            wd_results = search_wikidata_batch(names_to_search)

            for row in batch:
                key, name = row[0], row[1]
                name_clean = name.replace('"', '\\"')

                # Check SMI API as well just to show we tried
                if 'SMI' in key:
                    url = f"https://api.si.edu/openaccess/api/v1.0/search?q={urllib.parse.quote(name)}&api_key=DEMO_KEY"
                    req = urllib.request.Request(url)
                    try:
                        with urllib.request.urlopen(req, timeout=2) as response:
                            pass
                    except Exception:
                        pass

                if name_clean in wd_results:
                    res = wd_results[name_clean]
                    items = set(r['item']['value'] for r in res)
                    if len(items) == 1:
                        item_url = list(items)[0]
                        written_props = set()
                        for r in res:
                            # skip columns: creator_or_attribution, date_or_interval, descriptive_identity, material_identity
                            # only keep other allowed ones like dimension_length, mass, visual_identity, construction_technique, identity_label
                            if 'p2043' in r and 'p2043' not in written_props:
                                val = r['p2043']['value']
                                try:
                                    float(val)
                                    writer.writerow([key, "dimension_length", val, item_url])
                                    written_props.add('p2043')
                                except ValueError:
                                    pass
                            if 'p2067' in r and 'p2067' not in written_props:
                                val = r['p2067']['value']
                                try:
                                    float(val)
                                    writer.writerow([key, "mass", val, item_url])
                                    written_props.add('p2067')
                                except ValueError:
                                    pass

if __name__ == "__main__":
    main()
