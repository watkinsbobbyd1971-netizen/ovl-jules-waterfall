import json

in_file = "output/profile-ACC_01/batch_04_CAT01_2010S_R06-10_v3.jsonl"
lines = []
with open(in_file, 'r') as f:
    for line in f:
        lines.append(json.loads(line))

with open("pr_desc.txt", "w") as f:
    f.write(f"N = {len(lines)}\n\n")
    for b in lines:
        f.write(f"{b['canonical_dedup_key']} | {b['verification_citation_url']}\n")
