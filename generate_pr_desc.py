import json

file_path = 'output/profile-ACC_06/batch_04_CAT19_2020S_R06-10_v3.jsonl'
with open(file_path, 'r') as f:
    lines = f.readlines()

blocks = [json.loads(line) for line in lines]
n = len(blocks)

with open('pr_desc.txt', 'w') as f:
    f.write(f"{n}\n")
    for b in blocks:
        f.write(f"{b['canonical_dedup_key']} | {b['verification_citation_url']}\n")
