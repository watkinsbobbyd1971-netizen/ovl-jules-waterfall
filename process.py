import csv
import gzip
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

INPUT_FILE = "tasks/reptile_fish/chunk-0003.csv.gz"
OUTPUT_DIR = "out/reptile_fish"
OUTPUT_CSV = f"{OUTPUT_DIR}/chunk-0003.csv"
OUTPUT_NOTES = f"{OUTPUT_DIR}/chunk-0003.notes.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_gbif(name):
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(name)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get('matchType') == 'EXACT':
                # double check exact match of name
                if 'scientificName' in data:
                    returned_name = data['scientificName'].lower()
                    if returned_name == name.lower() or returned_name.startswith(name.lower() + " "): # Account for author in scientificName
                        return {'source': url, 'data': data}
                    if 'canonicalName' in data and data['canonicalName'].lower() == name.lower():
                        return {'source': url, 'data': data}
    except Exception as e:
        pass
    return None

def fetch_wikidata(name):
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(name)}&language=en&format=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get('search'):
                # Just return exact match if first result matches
                first = data['search'][0]
                if first.get('match', {}).get('type') == 'label' and first.get('label', '').lower() == name.lower():
                    # check for exact match in label or alias
                    return {'source': url, 'data': first}
    except Exception as e:
        pass
    return None

def process_subject(row):
    key, name = row
    results = []

    # Try GBIF
    gbif_res = fetch_gbif(name)
    if gbif_res:
        # Example: scientific_identity
        if 'scientificName' in gbif_res['data']:
            results.append({
                'canonical_dedup_key': key,
                'column_name': 'scientific_identity',
                'value': json.dumps(gbif_res['data']['scientificName']),
                'source_url': gbif_res['source']
            })

    # Try Wikidata
    wd_res = fetch_wikidata(name)
    if wd_res:
        # Example: identity_label
        results.append({
            'canonical_dedup_key': key,
            'column_name': 'identity_label',
            'value': json.dumps(wd_res['data']['label']),
            'source_url': wd_res['source']
        })

    return results

def main():
    rows = []
    with gzip.open(INPUT_FILE, 'rt', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # skip header
        for row in reader:
            if len(row) == 2:
                rows.append(row)

    all_results = []
    print(f"Processing {len(rows)} rows...")

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_subject, row): row for row in rows}
        for i, future in enumerate(as_completed(futures)):
            if i % 100 == 0:
                print(f"Processed {i}/{len(rows)}")
            res = future.result()
            if res:
                all_results.extend(res)

    print(f"Found {len(all_results)} values.")

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        for r in all_results:
            writer.writerow([r['canonical_dedup_key'], r['column_name'], r['value'], r['source_url']])

    with open(OUTPUT_NOTES, 'w', encoding='utf-8') as f:
        f.write("Attempted sources:\n")
        f.write("- GBIF Species Match API (https://api.gbif.org/v1/species/match) for biological taxonomy and scientific identity.\n")
        f.write("- Wikidata Action API (wbsearchentities) for general identity labels.\n")

if __name__ == "__main__":
    main()
