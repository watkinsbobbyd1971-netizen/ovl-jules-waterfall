#!/usr/bin/env python3
"""
OVL v3.0.0 Cloud Waterfall Compiler for Google Jules (60 Cloud VMs x 6 Profiles).
Writes strictly to branch/profile-isolated output files (output/{profile_slug}_v3.jsonl)
so parallel Jules PRs across profile-1..profile-6 never conflict on merge.
"""
import csv, hashlib, json, os, subprocess

def get_branch_slug() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
        return out.replace("/", "_") if out and out != "HEAD" else "main"
    except Exception:
        return "worker"

def compile_row(row: dict) -> dict:
    dims = [int(x) for x in str(row.get("dimensions_mm", "4500x1800x1400")).lower().split("x")]
    block = {
        "schema_version": "3.0.0",
        "block_type": "MAN_MADE_MASTER",
        "source_lib_id": row["record_id"],
        "dedup_key": row["dedup_key"],
        "subject": row["subject"],
        "category_code": row["category_code"],
        "region_code": row["region_code"],
        "era_code": row["era_code"],
        "year": int(row["year"]),
        "verification_citation_url": row["citation_url"],
        "dimensions_mm": {
            "length_mm": dims[0],
            "width_mm": dims[1],
            "height_mm": dims[2],
        },
        "mass_grams": {"curb_mass_g": int(row["mass_g"])},
    }
    block["sha256"] = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
    return block

def main():
    os.makedirs("output", exist_ok=True)
    slug = get_branch_slug()
    out_path = os.path.join("output", f"{slug}_v3.jsonl")
    blocks = []
    if os.path.exists("queue_batch_01.csv"):
        with open("queue_batch_01.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                blocks.append(compile_row(row))
    with open(out_path, "w", encoding="utf-8") as out_f:
        for b in blocks:
            out_f.write(json.dumps(b) + "\n")
    print(f"Compiled {len(blocks)} v3.0.0 blocks -> {out_path}")

if __name__ == "__main__":
    main()
