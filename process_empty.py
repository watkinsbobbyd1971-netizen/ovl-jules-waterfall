import csv
import gzip
import os

category = 'mineral_material'
chunk_id = '0021'
input_file = f'tasks/{category}/chunk-{chunk_id}.csv.gz'
output_file = f'out/{category}/chunk-{chunk_id}.csv'

os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w') as f:
    f.write('canonical_dedup_key,column_name,value,source_url\n')
