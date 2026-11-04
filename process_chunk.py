import csv
import gzip
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_gbif(subject_name, dedup_key):
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(subject_name)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data.get('matchType') in ['EXACT', 'FUZZY'] and 'scientificName' in data:
                return data, url
    except Exception:
        pass
    return None, None

def process_row(row):
    dedup_key = row['canonical_dedup_key']
    subject_name = row['subject_name']

    results = []

    gbif_data, url = fetch_gbif(subject_name, dedup_key)
    if gbif_data:
        canonical = gbif_data.get('canonicalName')
        scientific = gbif_data.get('scientificName')
        if canonical:
            results.append({
                'canonical_dedup_key': dedup_key,
                'column_name': 'scientific_identity',
                'value': canonical,
                'source_url': url
            })
            if scientific:
                # Extracts authority
                auth = scientific.replace(canonical, "").strip()
                if auth:
                    results.append({
                        'canonical_dedup_key': dedup_key,
                        'column_name': 'taxon_authority',
                        'value': auth,
                        'source_url': url
                    })
    return results

input_file = 'tasks/fungal_microbe/chunk-0077.csv.gz'
output_file = 'out/fungal_microbe/chunk-0077.csv'

with gzip.open(input_file, 'rt', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

all_results = []
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_row = {executor.submit(process_row, row): row for row in rows}
    for future in as_completed(future_to_row):
        res = future.result()
        if res:
            all_results.extend(res)

with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
    writer.writeheader()
    for res in all_results:
        writer.writerow(res)
