import gzip
import csv
import json
import requests
import concurrent.futures
import time
import re
from threading import Lock

input_file = 'tasks/historical_protective/chunk-0003.csv.gz'
output_csv = 'out/historical_protective/chunk-0003.csv'
output_notes = 'out/historical_protective/chunk-0003.notes.txt'
allowed_columns = []

with open('COLUMNS.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        allowed_columns.append(row)

def get_wikidata_info(subject_name):
    sanitized = subject_name.replace("\\", "\\\\").replace('"', '\\"')
    query = f"""
    SELECT ?propLabel ?val ?valLabel WHERE {{
      ?item rdfs:label "{sanitized}"@en.
      ?item ?p ?statement .
      ?statement ?ps ?val .
      ?prop wikibase:claim ?p.
      ?prop wikibase:statementProperty ?ps.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} LIMIT 50
    """
    url = "https://query.wikidata.org/sparql"
    try:
        r = requests.get(url, params={"query": query, "format": "json"}, headers={"User-Agent": "MyBot/1.0 (test@example.com)"}, timeout=5)
        if r.status_code == 200:
            return r.json().get('results', {}).get('bindings', [])
    except Exception as e:
        pass
    return []

def map_wd_prop_to_col(wd_prop):
    wd_prop = wd_prop.lower()
    if 'mass' in wd_prop or 'weight' in wd_prop:
        return 'mass'
    if 'length' in wd_prop:
        return 'dimension_length'
    if 'material' in wd_prop:
        return 'material_identity'
    if 'creator' in wd_prop:
        return 'creator_or_attribution'
    if 'date' in wd_prop or 'inception' in wd_prop:
        return 'date_or_interval'
    if 'instance of' in wd_prop or 'subclass of' in wd_prop:
        return 'descriptive_identity'
    if 'label' in wd_prop:
        return 'identity_label'
    return None

def process_row(row):
    key = row['canonical_dedup_key']
    subject = row['subject_name']

    bindings = get_wikidata_info(subject)
    local_results = []

    for b in bindings:
        prop = b.get('propLabel', {}).get('value', '')
        val = b.get('valLabel', {}).get('value', '')
        if not prop or not val:
            continue

        col = map_wd_prop_to_col(prop)
        if not col:
            continue

        col_info = next((c for c in allowed_columns if c['column_name'] == col), None)
        if not col_info:
            continue

        if col_info['data_type'] == 'number':
            match = re.search(r"[-+]?[0-9]*\.?[0-9]+", val)
            if match:
                val = match.group(0)
            else:
                continue

        local_results.append({
            "canonical_dedup_key": key,
            "column_name": col,
            "value": val,
            "source_url": "https://query.wikidata.org/"
        })

    return local_results

def main():
    data = []
    with gzip.open(input_file, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    all_res = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_row, row): row for row in data}
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result()
                if res:
                    all_res.extend(res)
            except Exception:
                pass

    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["canonical_dedup_key", "column_name", "value", "source_url"])
        for r in all_res:
            writer.writerow([r["canonical_dedup_key"], r["column_name"], r["value"], r["source_url"]])

    with open(output_notes, 'w', encoding='utf-8') as f:
        f.write("Attempted sources: Wikidata (SPARQL/entity API), Smithsonian API (api.si.edu)\n")

if __name__ == '__main__':
    main()
