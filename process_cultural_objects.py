import csv
import gzip
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def query_wikidata(subject_name):
    # Try to find exact matches on Wikidata
    encoded_query = urllib.parse.quote(subject_name)
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={encoded_query}&language=en&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0 (someone@example.com)'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if 'search' in data and data['search']:
                for item in data['search']:
                    # Must be an exact label match to avoid hallucinating
                    if item.get('label', '').lower() == subject_name.lower():
                        return item['id']
    except Exception as e:
        pass
    return None

def fetch_wikidata_properties(entity_id):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&languages=en&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0 (someone@example.com)'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if 'entities' in data and entity_id in data['entities']:
                return data['entities'][entity_id].get('claims', {})
    except Exception:
        pass
    return {}

def process_row(row):
    dedup_key = row['canonical_dedup_key']
    subject_name = row['subject_name']

    results = []

    entity_id = query_wikidata(subject_name)
    time.sleep(0.1) # basic rate limiting

    if entity_id:
        claims = fetch_wikidata_properties(entity_id)
        # Detailed logic based on COLUMNS.csv for cultural_object

        # P217: inventory number -> collection_object_identifier
        if 'P217' in claims:
            for claim in claims['P217']:
                val = claim.get('mainsnak', {}).get('datavalue', {}).get('value')
                if val:
                    results.append([dedup_key, 'collection_object_identifier', json.dumps(val), f"https://www.wikidata.org/wiki/{entity_id}"])

        # P170 (creator) or P176 (manufacturer) -> creator_or_attribution
        for prop in ['P170', 'P176']:
            if prop in claims:
                for claim in claims[prop]:
                    val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                    if val:
                        results.append([dedup_key, 'creator_or_attribution', json.dumps(val), f"https://www.wikidata.org/wiki/{entity_id}"])

        # P31 (instance of) or P279 (subclass of) -> descriptive_identity
        for prop in ['P31', 'P279']:
            if prop in claims:
                for claim in claims[prop]:
                    val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                    if val:
                        results.append([dedup_key, 'descriptive_identity', json.dumps(val), f"https://www.wikidata.org/wiki/{entity_id}"])

        # P186 (material used) -> material_identity
        if 'P186' in claims:
            for claim in claims['P186']:
                val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                if val:
                    results.append([dedup_key, 'material_identity', json.dumps(val), f"https://www.wikidata.org/wiki/{entity_id}"])

        # P2079 (fabrication method) -> technique
        if 'P2079' in claims:
            for claim in claims['P2079']:
                val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                if val:
                    results.append([dedup_key, 'technique', json.dumps(val), f"https://www.wikidata.org/wiki/{entity_id}"])

        # P2043 (length) -> dimension_length (convert to mm if needed, Wikidata usually uses Q-items for units,
        # but since we found no matches, we can add a basic extractor)

    return results

def main():
    input_file = "tasks/cultural_object/chunk-0016.csv.gz"
    output_file = "out/cultural_object/chunk-0016.csv"
    notes_file = "out/cultural_object/chunk-0016.notes.txt"

    rows = []
    with gzip.open(input_file, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    all_results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_row, row): row for row in rows}
        for i, future in enumerate(as_completed(futures)):
            if i % 100 == 0:
                print(f"Processed {i}/{len(rows)}")
            res = future.result()
            if res:
                all_results.extend(res)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        for res in all_results:
            writer.writerow(res)

    with open(notes_file, 'w', encoding='utf-8') as f:
        f.write("Queried Wikidata (wbsearchentities, wbgetentities) for exact string matches.\n")
        f.write("No other APIs used (Smithsonian Open Access requires API key, avoiding credentials).\n")
        f.write("Matches were filtered by exact subject name to avoid false positives.\n")

if __name__ == "__main__":
    main()
