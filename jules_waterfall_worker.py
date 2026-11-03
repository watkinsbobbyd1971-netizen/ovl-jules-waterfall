#!/usr/bin/env python3
"""
Self-Contained OVL v3.0.0 Cloud Waterfall Compiler for Google Jules.
Requires ZERO external API keys, ZERO network calls, and ZERO user questions.
Reads queue_batch_01.csv from the repository root and writes all output/*.jsonl files.
"""
import csv, json, os, hashlib

def build_batch():
    os.makedirs("output", exist_ok=True)
    if not os.path.exists("queue_batch_01.csv"):
        raise FileNotFoundError("queue_batch_01.csv missing in repo root")
    blocks = []
    with open("queue_batch_01.csv", "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            skey = (row.get("dedup_key") or row.get("canonical_dedup_key") or "").strip()
            if not skey:
                continue
            facts_raw = row.get("verified_facts") or "{}"
            try:
                facts = json.loads(facts_raw) if facts_raw else {}
            except Exception:
                facts = {}
            is_man_made = any(f"CAT{i:02d}" in skey or f"CAT_{i:02d}" in skey for i in range(1, 11))
            variant = "MAN_MADE_MASTER" if is_man_made else "ORGANIC_MASTER"
            block = {
                "schema_version": "3.0.0",
                "block_type": variant,
                "canonical_dedup_key": skey,
                "subject": (row.get("subject") or skey).strip(),
                "region_code": (row.get("region_code") or "REG_01").strip(),
                "era_code": (row.get("era_code") or "ERA_07").strip(),
                "exact_date_or_year": str(row.get("year") or "2015").strip(),
                "verification_citation_url": (row.get("primary_source_url") or "https://en.wikipedia.org").strip(),
                "verified_measurements": facts,
                "pbr_material_priors": {
                    "base_albedo_hex": "#7A7F85",
                    "metallic": 0.2 if is_man_made else 0.0,
                    "roughness": 0.45,
                    "ior": 1.5
                }
            }
            block["sha256"] = hashlib.sha256(json.dumps(block, sort_keys=True).encode("utf-8")).hexdigest()
            blocks.append(json.dumps(block))

    payload = "\n".join(blocks) + "\n"
    targets = [
        "output/batch_01_v3.jsonl",
        "output/profile-1-batch.jsonl",
        "output/profile-2-batch.jsonl",
        "output/profile-3-batch.jsonl",
        "output/profile-4-batch.jsonl",
        "output/profile-5-batch.jsonl",
    ]
    for t in targets:
        with open(t, "w", encoding="utf-8") as out:
            out.write(payload)
    print(f"SUCCESS: Compiled {len(blocks)} v3.0.0 blocks into {', '.join(targets)}")

if __name__ == "__main__":
    build_batch()
