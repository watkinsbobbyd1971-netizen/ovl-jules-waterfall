import json

count = 0
lines = []
with open("output/profile-ACC_02/batch_04_CAT06_2020S_R01-05_v3.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        block = json.loads(line)
        count += 1
        lines.append(f"{block['canonical_dedup_key']} | {block['verification_citation_url']}")

with open("pr_desc.txt", "w", encoding="utf-8") as f:
    f.write(f"{count} verified blocks\n")
    for line in lines:
        f.write(f"{line}\n")
