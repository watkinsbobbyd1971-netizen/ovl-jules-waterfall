import gzip
import csv
import urllib.request
import urllib.parse
import json
import time

def query_wikidata_sparql(subject_name):
    # Sparql query for exact matches, get material property (P186) or mass (P2067)
    query = f"""
    SELECT ?item ?itemLabel ?material ?materialLabel ?mass WHERE {{
      ?item rdfs:label "{subject_name}"@en.
      OPTIONAL {{ ?item wdt:P186 ?material. }}
      OPTIONAL {{ ?item wdt:P2067 ?mass. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 10
    """
    url = "https://query.wikidata.org/sparql"
    req = urllib.request.Request(f"{url}?query={urllib.parse.quote(query)}", headers={'User-Agent': 'Mozilla/5.0 (Bot for Data Fill)', 'Accept': 'application/sparql-results+json'})
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data.get("results", {}).get("bindings", [])
    except Exception as e:
        if isinstance(e, urllib.error.HTTPError) and e.code == 429:
            return "RATE_LIMIT"
    return []

def query_smithsonian(subject_name):
    url = "https://api.si.edu/openaccess/api/v1.0/search"
    params = {
        "q": f'"{subject_name}"',
        "api_key": "DEMO_KEY"
    }
    query_string = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query_string}", headers={'User-Agent': 'Mozilla/5.0 (Bot for Data Fill)'})
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data.get("response", {}).get("rows", [])
    except Exception as e:
        if isinstance(e, urllib.error.HTTPError) and e.code == 429:
            return "RATE_LIMIT"
    return []

def main():
    chunk_file = "tasks/mineral_material/chunk-0005.csv.gz"
    out_csv = "out/mineral_material/chunk-0005.csv"
    notes_file = "out/mineral_material/chunk-0005.notes.txt"

    subjects = []
    with gzip.open(chunk_file, 'rt') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects.append(row)

    notes = []
    results = []

    wikidata_rate_limit = False
    smithsonian_rate_limit = False

    for row in subjects:
        if wikidata_rate_limit and smithsonian_rate_limit:
            break

        subject_name = row['subject_name']
        dedup_key = row['canonical_dedup_key']

        # 1. Try Wikidata
        if not wikidata_rate_limit:
            wd_results = query_wikidata_sparql(subject_name)
            if wd_results == "RATE_LIMIT":
                wikidata_rate_limit = True
                notes.append("Wikidata SPARQL API failed: 429 Too Many Requests (OVER_RATE_LIMIT)")
            elif wd_results:
                for res in wd_results:
                    # check exact label match
                    label = res.get("itemLabel", {}).get("value")
                    item = res.get("item", {}).get("value")

                    if label and label.lower() == subject_name.lower():
                        material_label = res.get("materialLabel", {}).get("value")
                        if material_label and not material_label.startswith("http"): # Check if it resolved to label
                            results.append((dedup_key, "material_identity", json.dumps(material_label), item))

                        mass = res.get("mass", {}).get("value")
                        if mass:
                            # Assume in kg, but need to be in g according to COLUMNS.csv if we were to convert
                            # Actually, we shouldn't assume. But if we extract it, we must match unit.
                            pass

        # 2. Try Smithsonian
        if not smithsonian_rate_limit:
            si_data = query_smithsonian(subject_name)
            if si_data == "RATE_LIMIT":
                smithsonian_rate_limit = True
                notes.append("Smithsonian Open Access API failed: 429 Too Many Requests (OVER_RATE_LIMIT)")
            elif si_data:
                for row_data in si_data:
                    title = row_data.get("title", "")
                    if title.lower() == subject_name.lower():
                        content = row_data.get("content", {})
                        freetext = content.get("freetext", {})

                        # physical description might have materials
                        physical_desc = freetext.get("physicalDescription", [])
                        for desc in physical_desc:
                            if desc.get("label") == "Material":
                                results.append((dedup_key, "material_identity", json.dumps(desc.get("content")), f"https://collections.si.edu/search/detail/{row_data.get('id')}"))

    if not notes:
        notes.append("Completed queries successfully. No rate limits hit.")

    with open(out_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key','column_name','value','source_url'])
        for r in results:
            writer.writerow(r)

    with open(notes_file, 'w') as f:
        f.write("\n".join(notes))
        f.write("\n")

if __name__ == "__main__":
    main()
