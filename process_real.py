import csv
import gzip
import json

category = 'mineral_material'
chunk_id = '0021'
input_file = f'tasks/{category}/chunk-{chunk_id}.csv.gz'
output_file = f'out/{category}/chunk-{chunk_id}.csv'

chunk_keys = {}
with gzip.open(input_file, 'rt', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        chunk_keys[row['canonical_dedup_key']] = row['subject_name']

met_data = {}
with open('MetObjects.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        met_data[row['Object ID']] = row

out_rows = []
for key, subject in chunk_keys.items():
    if 'MET-' in key:
        obj_id = key.split('MET-')[-1]
        obj_id = str(int(obj_id)) # remove leading zeros
        if obj_id in met_data:
            met_row = met_data[obj_id]
            source_url = met_row.get('Link Resource', f'https://www.metmuseum.org/art/collection/search/{obj_id}')

            medium = met_row.get('Medium', '').strip()
            if medium:
                out_rows.append({
                    'canonical_dedup_key': key,
                    'column_name': 'material_identity',
                    'value': json.dumps(medium),
                    'source_url': source_url
                })

print(f"Found {len(out_rows)} rows to write.")
with open(output_file, 'w', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
    writer.writeheader()
    for row in out_rows:
        writer.writerow(row)
