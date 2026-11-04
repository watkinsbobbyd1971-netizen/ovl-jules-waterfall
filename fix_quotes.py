import csv

out_rows = []
with open("out/plant/chunk-0083.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        v = row["value"].replace('\\', '').replace('"', '')
        row["value"] = v
        out_rows.append(row)

with open("out/plant/chunk-0083.csv", "w", newline="") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_NONE, escapechar="\\")
    writer.writerow(["canonical_dedup_key", "column_name", "value", "source_url"])
    for row in out_rows:
        writer.writerow([row["canonical_dedup_key"], row["column_name"], f'"{row["value"]}"', row["source_url"]])
