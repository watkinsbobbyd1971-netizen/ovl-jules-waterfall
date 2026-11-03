import json
import hashlib

def compute_sha256(record):
    r_no_hash = {k: v for k, v in record.items() if k != 'sha256'}
    s = json.dumps(r_no_hash, sort_keys=True)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

blocks = []

# Harmony of the Seas
blocks.append({
    "schema_version": "3.0.0",
    "block_type": "MAN_MADE_MASTER",
    "canonical_dedup_key": "IDB-REG10-CAT08-ERA06-2015-HARMONY-OF-THE-SEAS",
    "subject": "Harmony of the Seas",
    "category_code": "CAT_08",
    "region_code": "REG_10",
    "era_code": "ERA_06",
    "exact_date_or_year": "19 June 2015",
    "year": 2015,
    "verification_citation_url": "https://en.wikipedia.org/wiki/Harmony_of_the_Seas",
    "dimensions_mm": {
        "length_mm": 362120.0,
        "width_mm": 66000.0,
        "height_mm": 22600.0
    },
    "mass_g": 1.2e11,
    "dimensional_specifications_mm_g": {
        "overall_bounding_box_mm": {
            "length_mm": 362120.0,
            "width_mm": 66000.0,
            "height_mm": 22600.0
        },
        "mass_and_tolerance": {
            "dry_mass_g": 1.2e11
        }
    },
    "mass_basis": "SOURCED",
    "lib_source": "OPEN-WEB",
    "acc_slot": "ACC_03",
    "pbr_material_priors": {
        "base_albedo_hex": "#7A7F85",
        "metallic": 0.2,
        "roughness": 0.45,
        "ior": 1.5
    }
})

# Allure of the Seas
blocks.append({
    "schema_version": "3.0.0",
    "block_type": "MAN_MADE_MASTER",
    "canonical_dedup_key": "IDB-REG10-CAT08-ERA06-2010-ALLURE-OF-THE-SEAS",
    "subject": "Allure of the Seas",
    "category_code": "CAT_08",
    "region_code": "REG_10",
    "era_code": "ERA_06",
    "exact_date_or_year": "28 October 2010",
    "year": 2010,
    "verification_citation_url": "https://en.wikipedia.org/wiki/Allure_of_the_Seas",
    "dimensions_mm": {
        "length_mm": 362000.0,
        "width_mm": 64900.0,
        "height_mm": 72000.0
    },
    "mass_g": 1e11,
    "dimensional_specifications_mm_g": {
        "overall_bounding_box_mm": {
            "length_mm": 362000.0,
            "width_mm": 64900.0,
            "height_mm": 72000.0
        },
        "mass_and_tolerance": {
            "dry_mass_g": 1e11
        }
    },
    "mass_basis": "SOURCED",
    "lib_source": "OPEN-WEB",
    "acc_slot": "ACC_03",
    "pbr_material_priors": {
        "base_albedo_hex": "#7A7F85",
        "metallic": 0.2,
        "roughness": 0.45,
        "ior": 1.5
    }
})

# Titan (submersible)
blocks.append({
    "schema_version": "3.0.0",
    "block_type": "MAN_MADE_MASTER",
    "canonical_dedup_key": "IDB-REG10-CAT08-ERA06-2018-TITAN-SUBMERSIBLE",
    "subject": "Titan (submersible)",
    "category_code": "CAT_08",
    "region_code": "REG_10",
    "era_code": "ERA_06",
    "exact_date_or_year": "2018",
    "year": 2018,
    "verification_citation_url": "https://en.wikipedia.org/wiki/Titan_(submersible)",
    "dimensions_mm": {
        "length_mm": 6700.0,
        "width_mm": 2800.0,
        "height_mm": 2500.0
    },
    "mass_g": 10432000.0,
    "dimensional_specifications_mm_g": {
        "overall_bounding_box_mm": {
            "length_mm": 6700.0,
            "width_mm": 2800.0,
            "height_mm": 2500.0
        },
        "mass_and_tolerance": {
            "dry_mass_g": 10432000.0
        }
    },
    "mass_basis": "SOURCED",
    "lib_source": "OPEN-WEB",
    "acc_slot": "ACC_03",
    "pbr_material_priors": {
        "base_albedo_hex": "#7A7F85",
        "metallic": 0.2,
        "roughness": 0.45,
        "ior": 1.5
    }
})

# RV Sikuliaq
blocks.append({
    "schema_version": "3.0.0",
    "block_type": "MAN_MADE_MASTER",
    "canonical_dedup_key": "IDB-REG10-CAT08-ERA06-2012-RV-SIKULIAQ",
    "subject": "RV Sikuliaq",
    "category_code": "CAT_08",
    "region_code": "REG_10",
    "era_code": "ERA_06",
    "exact_date_or_year": "13 October 2012",
    "year": 2012,
    "verification_citation_url": "https://en.wikipedia.org/wiki/RV_Sikuliaq",
    "dimensions_mm": {
        "length_mm": 79600.0,
        "width_mm": 15850.0,
        "height_mm": 8500.0
    },
    "mass_g": 3724000000.0,
    "dimensional_specifications_mm_g": {
        "overall_bounding_box_mm": {
            "length_mm": 79600.0,
            "width_mm": 15850.0,
            "height_mm": 8500.0
        },
        "mass_and_tolerance": {
            "dry_mass_g": 3724000000.0
        }
    },
    "mass_basis": "SOURCED",
    "lib_source": "OPEN-WEB",
    "acc_slot": "ACC_03",
    "pbr_material_priors": {
        "base_albedo_hex": "#7A7F85",
        "metallic": 0.2,
        "roughness": 0.45,
        "ior": 1.5
    }
})

# BRP Jose Rizal
blocks.append({
    "schema_version": "3.0.0",
    "block_type": "MAN_MADE_MASTER",
    "canonical_dedup_key": "IDB-REG06-CAT08-ERA06-2019-BRP-JOSE-RIZAL",
    "subject": "BRP Jose Rizal",
    "category_code": "CAT_08",
    "region_code": "REG_06",
    "era_code": "ERA_06",
    "exact_date_or_year": "23 May 2019",
    "year": 2019,
    "verification_citation_url": "https://en.wikipedia.org/wiki/BRP_Jose_Rizal",
    "dimensions_mm": {
        "length_mm": 107000.0,
        "width_mm": 13800.0,
        "height_mm": 6900.0
    },
    "mass_g": 2600000000.0,
    "dimensional_specifications_mm_g": {
        "overall_bounding_box_mm": {
            "length_mm": 107000.0,
            "width_mm": 13800.0,
            "height_mm": 6900.0
        },
        "mass_and_tolerance": {
            "dry_mass_g": 2600000000.0
        }
    },
    "mass_basis": "SOURCED",
    "lib_source": "OPEN-WEB",
    "acc_slot": "ACC_03",
    "pbr_material_priors": {
        "base_albedo_hex": "#7A7F85",
        "metallic": 0.2,
        "roughness": 0.45,
        "ior": 1.5
    }
})

# INS Vikrant (2013)
blocks.append({
    "schema_version": "3.0.0",
    "block_type": "MAN_MADE_MASTER",
    "canonical_dedup_key": "IDB-REG06-CAT08-ERA06-2013-INS-VIKRANT-2013",
    "subject": "INS Vikrant (2013)",
    "category_code": "CAT_08",
    "region_code": "REG_06",
    "era_code": "ERA_06",
    "exact_date_or_year": "12 August 2013",
    "year": 2013,
    "verification_citation_url": "https://en.wikipedia.org/wiki/INS_Vikrant_(2013)",
    "dimensions_mm": {
        "length_mm": 262500.0,
        "width_mm": 62000.0,
        "height_mm": 59000.0
    },
    "mass_g": 45000000000.0,
    "dimensional_specifications_mm_g": {
        "overall_bounding_box_mm": {
            "length_mm": 262500.0,
            "width_mm": 62000.0,
            "height_mm": 59000.0
        },
        "mass_and_tolerance": {
            "dry_mass_g": 45000000000.0
        }
    },
    "mass_basis": "SOURCED",
    "lib_source": "OPEN-WEB",
    "acc_slot": "ACC_03",
    "pbr_material_priors": {
        "base_albedo_hex": "#7A7F85",
        "metallic": 0.2,
        "roughness": 0.45,
        "ior": 1.5
    }
})

import os
os.makedirs("output/profile-ACC_03", exist_ok=True)
with open("output/profile-ACC_03/batch_04_CAT08_2010S_R06-10_v3.jsonl", "w", encoding="utf-8") as f:
    for b in blocks:
        b['sha256'] = compute_sha256(b)
        f.write(json.dumps(b) + "\n")
