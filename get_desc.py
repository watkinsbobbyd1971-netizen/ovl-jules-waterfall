import json

lines = []
with open('output/profile-ACC_01/batch_02_CAT03_2020S_R01-05_v3.jsonl', 'r') as f:
    for line in f:
        d = json.loads(line)
        lines.append(f"{d['canonical_dedup_key']} | {d['verification_citation_url']}")

with open('desc.txt', 'w') as f:
    f.write('\n'.join(lines))
