import csv
import json

with open('out/road_vehicle/chunk-0001.csv', 'r') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        assert row['canonical_dedup_key']
        assert row['column_name']
        assert row['value']
        assert row['source_url']
        try:
            json.loads(row['value'])
        except Exception as e:
            print(f"Row {i} has invalid JSON in value: {row['value']}")
            exit(1)
print("CSV fully valid!")
