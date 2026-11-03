import json

lines = []
with open("output/profile-ACC_03/batch_03_CAT07_2010S_R01-05_v3.jsonl") as f:
    for line in f:
        data = json.loads(line)
        lines.append(f"{data['canonical_dedup_key']} | {data['verification_citation_url']}")

print(f"30 verified blocks\n")
print("\n".join(lines))
