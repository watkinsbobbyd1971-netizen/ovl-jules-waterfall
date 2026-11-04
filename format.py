import csv

out_rows = []
with open("out/plant/chunk-0083.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # plain_text_in_json_column happens because they aren't properly double quoted JSON strings, or we removed them.
        # let's add them back carefully but ensure it parses correctly as JSON in the checker script
        v = row["value"]
        if not v.startswith('"'):
            v = f'"{v}"'
        row["value"] = v
        out_rows.append(row)

with open("out/plant/chunk-0083.csv", "w", newline="") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_NONE, escapechar="\\")
    writer.writerow(["canonical_dedup_key", "column_name", "value", "source_url"])
    for row in out_rows:
        writer.writerow([row["canonical_dedup_key"], row["column_name"], row["value"], row["source_url"]])
