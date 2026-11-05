import csv
import json

rows = []
with open('out/cultural_object/chunk-0093.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['column_name'] == 'technique':
            val = row['value']
            # Currently it is """val"""
            # strip all leading and trailing "
            val = val.strip('"')
            # Now we want JSON string as the rule dictates: "val"
            # We don't want CSV to quote it again, wait, if it's a JSON string, it contains quotes.
            # So CSV will write it as """val""" to escape the inner quotes! That is standard CSV representation of a JSON string.
            pass
        rows.append(row)
