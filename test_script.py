import csv
import json

def test_csv():
    with open('out/built_environment/chunk-0004.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert row['canonical_dedup_key']
            assert row['column_name']
            assert row['value']
            assert row['source_url']

            try:
                json.loads(row['value'])
            except json.JSONDecodeError:
                assert False, f"Value {row['value']} is not valid JSON"

if __name__ == '__main__':
    test_csv()
    print("Tests passed!")
