import gzip
import csv
import urllib.request
import urllib.parse
import json
import os
import time
import sys

def fetch_wikidata_item(item_id):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={item_id}&format=json&props=claims"
    headers = {'User-Agent': 'JulesBot/1.0 (https://example.com; jules@example.com)'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('entities', {}).get(item_id, {})
    except Exception:
        return {}

def extract_data():
    os.makedirs('out/electronics', exist_ok=True)

    out_csv_path = 'out/electronics/chunk-0007.csv'
    notes_path = 'out/electronics/chunk-0007.notes.txt'

    out_rows = []
    notes = []

    notes.append("Attempted to fetch data from Wikidata API (https://www.wikidata.org/w/api.php).")

    try:
        with gzip.open('tasks/electronics/chunk-0007.csv.gz', 'rt') as f:
            reader = csv.DictReader(f)
            subjects = list(reader)
    except Exception as e:
        print(f"Error reading input: {e}")
        return

    headers = {'User-Agent': 'JulesBot/1.0 (https://example.com; jules@example.com)'}

    rate_limited = False
    start_time = time.time()

    # Process all subjects, but break if we hit time limit or rate limit
    for row in subjects:
        if time.time() - start_time > 300: # 5 mins
            notes.append("Time limit reached during extraction.")
            break

        subject_name = row['subject_name']
        canonical_dedup_key = row['canonical_dedup_key']
        print(f"Querying Wikidata for: {subject_name}")

        # Search for the entity
        query_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(subject_name)}&language=en&format=json"

        try:
            req = urllib.request.Request(query_url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

                # Check for ambiguous matches - we want exact match
                if data.get('search'):
                    # Find exact match
                    exact_matches = [res for res in data['search'] if res.get('label', '').lower() == subject_name.lower()]

                    if len(exact_matches) == 1:
                        item_id = exact_matches[0]['id']
                        entity_data = fetch_wikidata_item(item_id)
                        claims = entity_data.get('claims', {})

                        source_url = f"https://www.wikidata.org/wiki/{item_id}"

                        # Mass (P2067)
                        if 'P2067' in claims:
                            for claim in claims['P2067']:
                                snak = claim.get('mainsnak', {})
                                if snak.get('datavalue', {}).get('type') == 'quantity':
                                    amount_str = snak['datavalue']['value']['amount']
                                    amount = float(amount_str)
                                    unit = snak['datavalue']['value']['unit']
                                    # Convert to g if possible
                                    if 'Q11570' in unit: # kilogram
                                        amount *= 1000
                                    elif 'Q41803' in unit: # gram
                                        pass
                                    else:
                                        continue # skip unknown unit
                                    out_rows.append([canonical_dedup_key, 'mass', json.dumps(amount), source_url])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"Rate limited on Wikidata for {subject_name}")
                rate_limited = True
                break
        except Exception as e:
            print(f"Error querying Wikidata for {subject_name}: {e}")

        time.sleep(1) # Be nice

    if rate_limited:
        notes.append("Encountered HTTP Error 429: Too Many Requests during extraction. Stopped execution.")

    with open(out_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        writer.writerows(out_rows)

    with open(notes_path, 'w') as f:
        f.write("\n".join(notes) + "\n")

if __name__ == '__main__':
    extract_data()
