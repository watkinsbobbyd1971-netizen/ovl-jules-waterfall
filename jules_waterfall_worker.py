#!/usr/bin/env python3
"""
Self-Contained OVL v3.0.0 Cloud Waterfall Compiler for Google Jules (Multi-Batch 9-Day Max-Out Edition).
Each profile writes ONLY to output/profile-N/batch_XX_v3.jsonl (N comes from the profile-N-* branch name),
so parallel profile branches never rewrite shared root files and their PRs never conflict.
Usage:
  python3 jules_waterfall_worker.py            # compiles every batch CSV found for this profile
  python3 jules_waterfall_worker.py 05         # compiles batch 05 only
  python3 jules_waterfall_worker.py 01 05      # compiles batches 01 through 05
  OVL_PROFILE=3 python3 jules_waterfall_worker.py 01   # override profile detection
Inputs (read-only): batches/profile-N/batch_XX.csv, else batches/batch_XX.csv, else queue_batch_XX.csv.
"""
import csv, json, os, re, sys, glob, hashlib, subprocess

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

def detect_profile():
    override = (os.environ.get("OVL_PROFILE") or "").strip()
    m = re.match(r"(?:profile-)?(\d+)(?:-|$)", override)
    if m:
        return int(m.group(1))
    refs = [os.environ.get("GITHUB_HEAD_REF"), os.environ.get("GITHUB_REF_NAME")]
    try:
        refs.append(subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip())
    except Exception:
        pass
    for ref in refs:
        m = re.match(r"profile-(\d+)(?:-|$)", ref or "")
        if m:
            return int(m.group(1))
    return None

def find_batch_csv(profile, b):
    for cpath in (f"batches/profile-{profile}/batch_{b:02d}.csv", f"batches/batch_{b:02d}.csv", f"queue_batch_{b:02d}.csv"):
        if os.path.exists(cpath):
            return cpath
    return None

def main():
    profile = detect_profile()
    if profile is None:
        print("Not a profile-N-* branch (set OVL_PROFILE=N to override); nothing compiled, shared output/ root files left untouched.")
        return
    out_dir = f"output/profile-{profile}"
    args = sys.argv[1:]
    if len(args) >= 2 and args[0].isdigit() and args[1].isdigit():
        batch_nums = list(range(int(args[0]), int(args[1]) + 1))
    elif len(args) == 1 and args[0].isdigit():
        batch_nums = [int(args[0])]
    else:
        found = glob.glob(f"batches/profile-{profile}/batch_*.csv") + glob.glob("batches/batch_*.csv") + glob.glob("queue_batch_*.csv")
        batch_nums = sorted({int(m.group(1)) for m in (re.search(r"batch_(\d+)\.csv$", p) for p in found) if m})
    total = 0
    for b in batch_nums:
        cpath = find_batch_csv(profile, b)
        if not cpath:
            print(f"No input CSV for batch {b:02d}; skipped")
            continue
        opath = f"{out_dir}/batch_{b:02d}_v3.jsonl"
        n = compile_csv_to_jsonl(cpath, opath)
        total += n
        print(f"Compiled {n} blocks from {cpath} -> {opath}")
    print(f"TOTAL COMPILED BLOCKS: {total}")

if __name__ == "__main__":
    main()
