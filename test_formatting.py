import csv
import json

data = [
    {"canonical_dedup_key": "123", "column_name": "manufacturer_or_creator", "value": json.dumps("Harley-Davidson"), "source_url": "https://www.wikidata.org/wiki/Q23208"}
]

with open("test_out.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["canonical_dedup_key", "column_name", "value", "source_url"])
    writer.writeheader()
    writer.writerows(data)
