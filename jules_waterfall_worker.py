#!/usr/bin/env python3
"""
Self-Contained OVL v3.0.0 Cloud Waterfall Compiler for Google Jules (Multi-Batch 9-Day Max-Out Edition).
Usage:
  python3 jules_waterfall_worker.py            # compiles queue_batch_01.csv + any specified batch
  python3 jules_waterfall_worker.py 01 05      # compiles batches/batch_01.csv through batches/batch_05.csv
"""
import csv, json, os, sys, glob, hashlib

def compile_csv_to_jsonl(csv_path, out_path):
    if not os.path.exists(csv_path):
        return 0
    blocks = []
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
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
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as out:
        out.write("\n".join(blocks) + "\n")
    return len(blocks)

def main():
    os.makedirs("output", exist_ok=True)
    args = sys.argv[1:]
    total = 0
    if len(args) >= 2 and args[0].isdigit() and args[1].isdigit():
        start_b, end_b = int(args[0]), int(args[1])
        for b in range(start_b, end_b + 1):
            cpath = f"batches/batch_{b:02d}.csv"
            opath = f"output/batch_{b:02d}_v3.jsonl"
            n = compile_csv_to_jsonl(cpath, opath)
            total += n
            print(f"Compiled {n} blocks -> {opath}")
    elif len(args) == 1 and args[0].isdigit():
        b = int(args[0])
        cpath = f"batches/batch_{b:02d}.csv"
        opath = f"output/batch_{b:02d}_v3.jsonl"
        total += compile_csv_to_jsonl(cpath, opath)
        print(f"Compiled {total} blocks -> {opath}")
    else:
        for bpath in sorted(glob.glob("batches/batch_*.csv")):
            bname = os.path.splitext(os.path.basename(bpath))[0]
            opath = f"output/{bname}_v3.jsonl"
            n = compile_csv_to_jsonl(bpath, opath)
            total += n
            print(f"Compiled {n} blocks -> {opath}")
        if os.path.exists("queue_batch_01.csv"):
            n = compile_csv_to_jsonl("queue_batch_01.csv", "output/batch_01_v3.jsonl")
            total += n
    print(f"TOTAL COMPILED BLOCKS: {total}")

if __name__ == "__main__":
    main()
