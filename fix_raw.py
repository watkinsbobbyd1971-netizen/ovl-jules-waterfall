import csv
import json
import re

rows = []
with open('out/cultural_object/chunk-0093.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['column_name'] == 'technique':
            val = row['value']
            # if it starts and ends with ", strip them
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            # Since check_output --fix formatted it, it might be JSON string literal
            try:
                if val.startswith('"') and val.endswith('"'):
                    val = json.loads(val)
                else:
                    val = json.loads(f'"{val}"')
            except:
                pass
            # Write raw unquoted string values for check_output.py --fix to process
            row['value'] = val
        rows.append(row)

with open('out/cultural_object/chunk-0093.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
    writer.writeheader()
    writer.writerows(rows)
