import urllib.request
import urllib.parse
import json
import gzip
import csv
import time
import concurrent.futures
import os

def fetch_with_retry(url, max_retries=10):
    req = urllib.request.Request(url, headers={'User-Agent': 'CoolBot/3.0 (someone@example.com)'})
    for i in range(max_retries):
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            if '429' in str(e) or '502' in str(e) or '503' in str(e):
                time.sleep((i + 1) * 2)
            else:
                return None
    return None

def process_subject(row):
    key = row['canonical_dedup_key']
    subject = row['subject_name']

    search_url = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=" + urllib.parse.quote(subject) + "&language=en&format=json"
    search_data = fetch_with_retry(search_url)

    out_rows = []

    if search_data and search_data.get('search'):
        item_id = search_data['search'][0]['id']
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={item_id}&format=json&props=claims|labels|descriptions"
        data = fetch_with_retry(url)

        if data and 'entities' in data and item_id in data['entities']:
            entity = data['entities'][item_id]
            claims = entity.get('claims', {})
            source_url = f"https://www.wikidata.org/wiki/{item_id}"

            labels = entity.get('labels', {})
            if 'en' in labels:
                out_rows.append([key, 'identity_label', labels['en']['value'], source_url])

            descriptions = entity.get('descriptions', {})
            if 'en' in descriptions:
                out_rows.append([key, 'descriptive_identity', descriptions['en']['value'], source_url])

            if 'P131' in claims:
                for claim in claims['P131']:
                    val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                    if val:
                        loc_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={val}&format=json&props=labels"
                        loc_data = fetch_with_retry(loc_url)
                        if loc_data:
                            loc_label = loc_data['entities'][val].get('labels', {}).get('en', {}).get('value')
                            if loc_label:
                                out_rows.append([key, 'location', loc_label, source_url])

            if 'P571' in claims:
                for claim in claims['P571']:
                    val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('time')
                    if val:
                        if val.startswith('+'):
                            val = val[1:11]
                            if val.endswith('-00-00'):
                                val = val[:4]
                        out_rows.append([key, 'construction_date', val, source_url])

            if 'P84' in claims:
                for claim in claims['P84']:
                    val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                    if val:
                        arch_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={val}&format=json&props=labels"
                        arch_data = fetch_with_retry(arch_url)
                        if arch_data:
                            arch_label = arch_data['entities'][val].get('labels', {}).get('en', {}).get('value')
                            if arch_label:
                                out_rows.append([key, 'creator_or_attribution', arch_label, source_url])
    return out_rows

def main():
    in_file = "tasks/built_environment/chunk-0079.csv.gz"
    out_file = "out/built_environment/chunk-0079.csv"

    with gzip.open(in_file, 'rt') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Total rows: {len(rows)}")

    processed_keys = set()
    if os.path.exists(out_file):
        with open(out_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_keys.add(row['canonical_dedup_key'])

    rows_to_process = [r for r in rows if r['canonical_dedup_key'] not in processed_keys]
    print(f"Rows to process: {len(rows_to_process)}")

    mode = 'a' if os.path.exists(out_file) else 'w'
    with open(out_file, mode, newline='') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(process_subject, row): row for row in rows_to_process}
            count = 0
            for future in concurrent.futures.as_completed(futures):
                count += 1
                if count % 20 == 0:
                    print(f"Processed {count}/{len(rows_to_process)}")
                res = future.result()
                if res:
                    for r in res:
                        writer.writerow(r)
                    f.flush()

if __name__ == '__main__':
    main()
