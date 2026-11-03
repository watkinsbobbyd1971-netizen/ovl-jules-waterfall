echo '33'
jq -r '"\(.canonical_dedup_key) | \(.verification_citation_url)"' output/profile-ACC_03/batch_03_CAT10_2020S_R01-05_v3.jsonl
