#!/usr/bin/env python3
"""
OVL v3.0.0 Cloud Waterfall Compiler for Google Jules (60 Cloud VMs x 5 Profiles).
Covers all 20 Categories (CAT_01..CAT_20), all 10 Global Regions (REG_01..REG_10),
2020-2026 Modern rows, 2010-2019 Claude/Muse rows, and OVL-Gemini-Chunks LIB files.
"""
import json, hashlib

PROFILE_ASSIGNMENTS = {
    "profile-1": ["CAT_01", "CAT_02", "CAT_03", "CAT_04"],
    "profile-2": ["CAT_05", "CAT_06", "CAT_07", "CAT_08"],
    "profile-3": ["CAT_09", "CAT_10", "CAT_11", "CAT_12"],
    "profile-4": ["CAT_13", "CAT_14", "CAT_15", "CAT_16"],
    "profile-5": ["CAT_17", "CAT_18", "CAT_19", "CAT_20"],
}
REGIONS = [f"REG_{i:02d}" for i in range(1, 11)]

def compile_compact_row(pipe_row: str) -> dict:
    parts = [p.strip() for p in pipe_row.split("|")]
    rec_id, skey, subject, cat, reg, era, year, dims, mass_g, url = parts[:10]
    l_mm, w_mm, h_mm = [int(x) for x in dims.split("x")]
    block = {
        "schema_version": "3.0.0",
        "block_type": "MAN_MADE_MASTER",
        "source_lib_id": rec_id,
        "dedup_key": skey,
        "subject": subject,
        "category_code": cat,
        "region_code": reg,
        "era_code": era,
        "year": int(year),
        "verification_citation_url": url,
        "dimensions_mm": {"length_mm": l_mm, "width_mm": w_mm, "height_mm": h_mm},
        "mass_grams": {"curb_mass_g": int(mass_g)},
    }
    block["sha256"] = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
    return block
