import urllib.request
import urllib.parse
import json
import gzip
import csv
import os
import concurrent.futures
import time

def process_subject(item_tuple):
    canonical_key, subject_name = item_tuple

    search_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(subject_name)}&language=en&format=json"
    req = urllib.request.Request(search_url, headers={'User-Agent': 'MyBot/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            search_data = json.loads(response.read().decode())
    except Exception:
        return []

    if not search_data.get('search'):
        return []

    results = []
    for item in search_data['search']:
        if item.get('match', {}).get('text', '').lower() == subject_name.lower() or item.get('label', '').lower() == subject_name.lower():
            entity_id = item['id']
            results.append((canonical_key, subject_name, entity_id))
            break # only care about exact matches

    time.sleep(0.01)
    return results

subjects = []
with gzip.open("tasks/historical_protective/chunk-0006.csv.gz", "rt") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        subjects.append((row[0], row[1]))

found = []
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(process_subject, s): s for s in subjects[:100]} # Test 100
    for future in concurrent.futures.as_completed(futures):
        res = future.result()
        if res:
            found.extend(res)

for f in found:
    print(f)
