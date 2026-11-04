import csv
import gzip
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys

INPUT_FILE = "tasks/fungal_microbe/chunk-0012.csv.gz"
OUTPUT_FILE = "out/fungal_microbe/chunk-0012.csv"

def fetch_gbif(subject_name):
    # Some subjects might have numbers or 'aff.' or similar, so strict=false might be better but let's see.
    # For now, just URL encode the raw string.
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(subject_name)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('matchType') == 'EXACT':
                if data.get('kingdom') in ['Fungi', 'Bacteria', 'Chromista', 'Protozoa', 'Archaea']:
                    return data
    except Exception as e:
        print(f"Error fetching {subject_name}: {e}")
    return None

def fetch_details(usage_key):
    url = f"https://api.gbif.org/v1/species/{usage_key}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching details {usage_key}: {e}")
    return None

def process_row(row):
    subject = row['subject_name']
    match = fetch_gbif(subject)
    results = []

    if match:
        usage_key = match['usageKey']
        url = f"https://api.gbif.org/v1/species/{usage_key}"
        details = fetch_details(usage_key)

        # scientific_identity
        if details and details.get('scientificName'):
            results.append({
                'canonical_dedup_key': row['canonical_dedup_key'],
                'column_name': 'scientific_identity',
                'value': json.dumps(details['scientificName']),
                'source_url': url
            })
        elif match.get('scientificName'):
            results.append({
                'canonical_dedup_key': row['canonical_dedup_key'],
                'column_name': 'scientific_identity',
                'value': json.dumps(match['scientificName']),
                'source_url': url
            })

        # taxon_authority
        if details and details.get('authorship'):
            results.append({
                'canonical_dedup_key': row['canonical_dedup_key'],
                'column_name': 'taxon_authority',
                'value': json.dumps(details['authorship']),
                'source_url': url
            })

        # descriptive_identity
        ranks = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus']
        desc = [match[r] for r in ranks if r in match and match[r]]
        if desc:
            results.append({
                'canonical_dedup_key': row['canonical_dedup_key'],
                'column_name': 'descriptive_identity',
                'value': json.dumps(" > ".join(desc)),
                'source_url': url
            })
    return results

def main():
    with gzip.open(INPUT_FILE, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    all_results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_row, row): row for row in rows}
        count = 0
        for future in as_completed(futures):
            try:
                res = future.result()
                all_results.extend(res)
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count}/{len(rows)}", flush=True)
            except Exception as e:
                print(f"Error processing row: {e}", flush=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        writer.writeheader()
        for res in all_results:
            writer.writerow(res)

    print(f"Wrote {len(all_results)} values to {OUTPUT_FILE}", flush=True)

if __name__ == "__main__":
    main()
