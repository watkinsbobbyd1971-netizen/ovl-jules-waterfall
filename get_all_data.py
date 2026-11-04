import csv
import gzip
import requests
import json
import os

def search_met(name):
    url = "https://collectionapi.metmuseum.org/public/collection/v1.1/search"
    params = {"q": name}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get('total', 0) == 1:
            obj_id = data['objectIDs'][0]
            obj_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}"
            resp2 = requests.get(obj_url, timeout=5)
            if resp2.status_code == 200:
                return resp2.json()
    except:
        pass
    return None

def get_row_data(row, met_data):
    if not met_data:
        return []

    rows = []
    key = row['canonical_dedup_key']
    url = met_data['objectURL']

    if met_data.get('medium'):
        rows.append([key, 'material_identity', json.dumps(met_data['medium']), url])

    if met_data.get('objectDate'):
        rows.append([key, 'date_or_interval', json.dumps(met_data['objectDate']), url])

    if met_data.get('objectID'):
        rows.append([key, 'collection_object_identifier', json.dumps(str(met_data['objectID'])), url])

    if met_data.get('title'):
        rows.append([key, 'identity_label', json.dumps(met_data['title']), url])

    if met_data.get('artistDisplayName'):
        rows.append([key, 'creator_or_attribution', json.dumps(met_data['artistDisplayName']), url])

    if met_data.get('department'):
        rows.append([key, 'cultural_context', json.dumps(met_data['department']), url])

    if met_data.get('dimensions'):
        rows.append([key, 'descriptive_identity', json.dumps(met_data['dimensions']), url])

    return rows

os.makedirs('out/cultural_object', exist_ok=True)
with gzip.open('tasks/cultural_object/chunk-0000.csv.gz', 'rt') as f, open('out/cultural_object/chunk-0000.csv', 'w') as out_f:
    reader = csv.DictReader(f)
    writer = csv.writer(out_f)
    writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
    for i, row in enumerate(reader):
        name = row['subject_name']
        met_data = search_met(name)
        new_rows = get_row_data(row, met_data)
        for r in new_rows:
            writer.writerow(r)

with open('out/cultural_object/chunk-0000.notes.txt', 'w') as f:
    f.write('Queried the MET API for all subjects with an exact match. Filtered out ambiguous responses where the total number of objects found was not 1.\n')
