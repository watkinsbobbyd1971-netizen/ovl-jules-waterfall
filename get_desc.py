import json

desc = "5\n"
with open('output/profile-ACC_04/batch_03_CAT12_2020S_R01-05_v3.jsonl') as f:
    for line in f:
        data = json.loads(line)
        desc += f"{data['canonical_dedup_key']} | {data['verification_citation_url']}\n"
print(desc)
