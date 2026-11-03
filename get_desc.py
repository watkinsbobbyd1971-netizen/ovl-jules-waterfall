import json

outfile = 'output/profile-ACC_02/batch_03_CAT04_2020S_R01-05_v3.jsonl'
lines = []
with open(outfile, 'r') as f:
    for line in f:
        data = json.loads(line)
        lines.append(f"{data['canonical_dedup_key']} | {data['verification_citation_url']}")

print(f"30")
for line in lines:
    print(line)
