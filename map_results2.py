import csv
import gzip
import json

with open('filtered_wd_map.json') as f:
    wd_map = json.load(f)

with open('wd_props.json') as f:
    wd_props = json.load(f)

subjects = []
with gzip.open('tasks/machinery/chunk-0022.csv.gz', 'rt') as f:
    reader = csv.DictReader(f)
    for row in reader:
        subjects.append(row)

prop_to_col = {
    'P527': 'component_relationship',
    'P31': 'descriptive_identity',
    'P279': 'descriptive_identity',
    'P2043': 'dimension_length',
    'P170': 'manufacturer_or_creator',
    'P176': 'manufacturer_or_creator',
    'P2067': 'mass',
    'P186': 'material_identity',
    'P2791': 'rated_power',
    'P2874': 'model_identifier'
}

output_rows = []

for subject in subjects:
    dedup_key = subject['canonical_dedup_key']
    name = subject['subject_name']

    if name in wd_map:
        wd_id = wd_map[name]
        props = wd_props.get(wd_id, {})

        url = f"https://www.wikidata.org/wiki/{wd_id}"

        for p, vals in props.items():
            if p in prop_to_col:
                col = prop_to_col[p]

                seen = set()

                for val in vals:
                    if col == 'dimension_length':
                        try:
                            val_float = float(val) * 1000
                            final_val = json.dumps(val_float)
                        except:
                            continue
                    elif col == 'mass':
                        try:
                            val_float = float(val) * 1000
                            final_val = json.dumps(val_float)
                        except:
                            continue
                    elif col == 'rated_power':
                        try:
                            final_val = json.dumps(float(val))
                        except:
                            continue
                    else:
                        final_val = json.dumps(val)

                    if final_val not in seen:
                        seen.add(final_val)
                        output_rows.append({
                            'canonical_dedup_key': dedup_key,
                            'column_name': col,
                            'value': final_val,
                            'source_url': url
                        })

print(f"Generated {len(output_rows)} property rows")

with open('out/machinery/chunk-0022.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
    writer.writeheader()
    for row in output_rows:
        writer.writerow(row)
