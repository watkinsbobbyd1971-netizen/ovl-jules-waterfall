#!/usr/bin/env python3
"""Validate one Jules batch file (JSONL) before committing it. Job J-20261101-CORPUS-AUTO.

Every line is checked the way the fleet staged-loader will check it on the way to BigQuery
(compact record -> IMAGE_DATA_BLOCK v3 -> fleet v3 validator), plus slice and anti-filler rules.
Exit code 0 only when EVERY line passes. Fix or drop failing lines, then run it again.

Usage:
  python3 tools/validate_jules_batch.py output/profile-ACC_01/batch_02_CAT01_2020S_R01-05_v3.jsonl \
      --cat CAT_01 --years 2020-2026 --regions 1-5
"""
import argparse, hashlib, json, math, re, sys

CATEGORY_NAMES = {
    'CAT_01': 'Architecture, Buildings & Civil Infrastructure', 'CAT_02': 'Interior Spaces, Furniture & Architectural Fixtures',
    'CAT_03': 'Industrial Machinery, Heavy Equipment & Power Systems', 'CAT_04': 'Computing, Electronics, Semiconductors & Telecom Hardware',
    'CAT_05': 'Hand Tools, Scientific Instruments & Horology', 'CAT_06': 'Historical & Modern Defense, Armor & Ballistic Systems',
    'CAT_07': 'Ground Vehicles, Automobiles, Locomotives & Rolling Stock', 'CAT_08': 'Maritime Vessels, Submersibles & Nautical Engineering',
    'CAT_09': 'Aerospace Vehicles, Satellites, Rockets & Avionics', 'CAT_10': 'Everyday Consumer Goods, Textiles, Apparel & Cultural Artifacts',
    'CAT_11': 'Human Anatomy, Somatotypes & Anthropometric Structures', 'CAT_12': 'Mammals & Terrestrial Vertebrates',
    'CAT_13': 'Reptiles, Amphibians, Fish & Marine Invertebrates', 'CAT_14': 'Birds / Avian Fauna & Feather Morphometrics',
    'CAT_15': 'Insects, Arachnids & Terrestrial Arthropods', 'CAT_16': 'Trees, Vascular Plants, Flowers & Botanical Structures',
    'CAT_17': 'Fungi, Lichens, Bryophytes, Algae & Micro-Organisms', 'CAT_18': 'Rocks, Minerals, Crystals, Gems & Fossil Specimens',
    'CAT_19': 'Landforms, Geomorphology, Soils & Planetary Terrain', 'CAT_20': 'Weather, Atmospheric Optics, Fire, Fluid & Astronomic Phenomena'}
REGION_NAMES = {
    'REG_01': 'North America', 'REG_02': 'Latin America & Caribbean', 'REG_03': 'Western & Northern Europe',
    'REG_04': 'Eastern Europe & Russia', 'REG_05': 'East Asia', 'REG_06': 'South & Southeast Asia',
    'REG_07': 'Middle East & North Africa', 'REG_08': 'Sub-Saharan Africa', 'REG_09': 'Oceania & Pacific',
    'REG_10': 'Polar, Oceanic & Orbital'}
KEY_RE = re.compile(r'IDB-REG(0[1-9]|10)-CAT(\d{2})-ERA(\d{2})-(\d{4})-([A-Z0-9]+(?:-[A-Z0-9]+)*)')
BAD_URL = re.compile(r'(\?rec=|#rec|/wiki/CAT_|example\.(com|org)|placeholder|lorem)', re.I)
FILLER = re.compile(r'(HOP\d+|REC\d{3,}|PLACEHOLDER|LOREM|TBD|UNKNOWN|N/A|SUBJECT[ _-]?\d+|ITEM[ _-]?\d+|SAMPLE[ _-]?\d+)', re.I)
REQUIRED = ['schema_version', 'block_type', 'canonical_dedup_key', 'subject', 'category_code', 'region_code', 'era_code',
            'exact_date_or_year', 'year', 'verification_citation_url', 'dimensions_mm', 'mass_g', 'mass_basis', 'acc_slot', 'sha256']


def era_for(year):
    """Bobby's two eras: 2010-2019 -> ERA_06 (1980-2019 band), 2020-2026 -> ERA_07 (contemporary)."""
    return 'ERA_06' if year <= 2019 else 'ERA_07'


def validate_v3(record):  # fleet v3 validator (workers/corpus-waterfall/validator.py), unchanged logic
    for key, expected in [('schema_version', '3.0.0'), ('block_type', 'IMAGE_DATA_BLOCK'), ('unit_system', 'SI_MILLIMETERS_AND_GRAMS')]:
        if record.get(key) != expected:
            raise ValueError('invalid ' + key)
    if record.get('master_variant') not in ('MAN_MADE_MASTER', 'ORGANIC_MASTER'):
        raise ValueError('invalid master_variant')
    fields = ('canonical_dedup_key sha256_subject_signature category_code category_name region_code region_name era_code '
              'time_period_label decade exact_date_or_year source_provenance verification_citation_url').split()
    anchor = record.get('temporal_and_dedup_anchor')
    if not isinstance(anchor, dict) or any(anchor.get(k) in (None, '') for k in fields):
        raise ValueError('missing temporal_and_dedup_anchor fields')
    for keys, kind in [(('dimensional_specifications_mm_g', 'morphometric_specifications_mm_g'), dict),
                       (('pbr_material_and_surface_physics', 'integument_and_subsurface_physics'), list),
                       (('structural_3d_hierarchy_and_mesh_priors', 'skeletal_rigging_and_3d_reconstruction_priors'), dict)]:
        if not any(isinstance(record.get(k), kind) and record[k] for k in keys):
            raise ValueError('missing/invalid ' + '/'.join(keys))

    def numbers(x):
        if isinstance(x, dict): return bool(x) and all(numbers(i) for i in x.values())
        if isinstance(x, list): return bool(x) and all(numbers(i) for i in x)
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)

    def numeric(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if k.endswith(('_mm', '_g')) and not numbers(v):
                    raise ValueError('nonnumeric ' + k)
                numeric(v)
        elif isinstance(value, list):
            for v in value: numeric(v)
    numeric(record)


def pos(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
        raise ValueError(what + ' must be a positive number')
    return v


def check(rec, a):
    miss = [k for k in REQUIRED if rec.get(k) in (None, '')]
    if miss:
        raise ValueError('missing ' + ','.join(miss))
    organic = int(rec['category_code'][4:]) >= 11 if re.fullmatch(r'CAT_\d{2}', str(rec['category_code'])) else None
    if organic is None or rec['category_code'] not in CATEGORY_NAMES:
        raise ValueError('invalid category_code')
    if rec['schema_version'] != '3.0.0':
        raise ValueError('schema_version must be 3.0.0')
    if rec['block_type'] != ('ORGANIC_MASTER' if organic else 'MAN_MADE_MASTER'):
        raise ValueError('block_type must be ' + ('ORGANIC_MASTER' if organic else 'MAN_MADE_MASTER'))
    if a.cat and rec['category_code'] != a.cat:
        raise ValueError('category outside this slice')
    if rec['region_code'] not in REGION_NAMES:
        raise ValueError('invalid region_code')
    if a.regions and int(rec['region_code'][4:]) not in a.regions:
        raise ValueError('region outside this slice')
    y = rec['year']
    if not isinstance(y, int) or isinstance(y, bool):
        raise ValueError('year must be an integer')
    if a.years and not (a.years[0] <= y <= a.years[1]):
        raise ValueError('year outside this slice')
    if str(y) not in str(rec['exact_date_or_year']):
        raise ValueError('exact_date_or_year does not contain year')
    if rec['era_code'] != era_for(y):
        raise ValueError('era_code must be %s for year %d' % (era_for(y), y))
    m = KEY_RE.fullmatch(rec['canonical_dedup_key'])
    if not m:
        raise ValueError('key must match IDB-REGnn-CATnn-ERAnn-YYYY-SUBJECT-SLUG (uppercase A-Z0-9 and hyphens)')
    if ('REG_' + m[1], 'CAT_' + m[2], 'ERA_' + m[3], int(m[4])) != (rec['region_code'], rec['category_code'], rec['era_code'], y):
        raise ValueError('key disagrees with region_code/category_code/era_code/year')
    for u in [rec['verification_citation_url']] + ([rec['source_2_url']] if rec.get('source_2_url') else []):
        if not isinstance(u, str) or not re.match(r'https://[^/\s]+/\S+', u) or BAD_URL.search(u):
            raise ValueError('citation must be a specific https page (no homepage, ?rec=, #rec, wiki/CAT_): %r' % u)
        if re.fullmatch(r'https://[^/]+/?(index\.html?|home|en/?)?', u, re.I):
            raise ValueError('citation is a homepage: %r' % u)
    if FILLER.search(rec['subject']) or FILLER.search(m[5]) or len(rec['subject'].strip()) < 3:
        raise ValueError('subject looks like filler/placeholder')
    d = rec['dimensions_mm']
    if not isinstance(d, dict):
        raise ValueError('dimensions_mm must be an object')
    L, W, H = (pos(d.get(k), 'dimensions_mm.' + k) for k in ('length_mm', 'width_mm', 'height_mm'))
    mass = pos(rec['mass_g'], 'mass_g')
    if not (rec['mass_basis'] == 'SOURCED' or str(rec['mass_basis']).startswith('DERIVED: ')):
        raise ValueError('mass_basis must be "SOURCED" or start with "DERIVED: "')
    if organic:
        spec = rec.get('morphometric_specifications_mm_g') or {}
        bb, mg = spec.get('overall_bounding_box_mm') or {}, spec.get('mass_and_physiological_range') or {}
        want = [(bb.get('total_body_length_mm'), L), (bb.get('wingspan_or_canopy_spread_mm'), W),
                (bb.get('standing_height_mm'), H), (mg.get('mean_adult_mass_g'), mass)]
        fam = 'morphometric_specifications_mm_g'
    else:
        spec = rec.get('dimensional_specifications_mm_g') or {}
        bb, mg = spec.get('overall_bounding_box_mm') or {}, spec.get('mass_and_tolerance') or {}
        want = [(bb.get('length_mm'), L), (bb.get('width_mm'), W), (bb.get('height_mm'), H), (mg.get('dry_mass_g'), mass)]
        fam = 'dimensional_specifications_mm_g'
    if not spec or any(v is None or abs(float(v) - float(x)) > 1e-6 for v, x in want):
        raise ValueError(fam + ' must be present and equal dimensions_mm / mass_g')
    body = {k: v for k, v in rec.items() if k != 'sha256'}
    if rec['sha256'] != hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest():
        raise ValueError('sha256 does not recompute (sha256 of json.dumps(record_without_sha256, sort_keys=True))')
    # compile exactly as the loader does and run the fleet v3 validator on the result
    key = rec['canonical_dedup_key']
    anchor = dict(canonical_dedup_key=key, sha256_subject_signature=hashlib.sha256(key.encode()).hexdigest(),
                  category_code=rec['category_code'], category_name=CATEGORY_NAMES[rec['category_code']],
                  region_code=rec['region_code'], region_name=REGION_NAMES[rec['region_code']], era_code=rec['era_code'],
                  time_period_label='x', decade=f'{(y // 10) * 10}s', exact_date_or_year=str(rec['exact_date_or_year']),
                  source_provenance='jules', verification_citation_url=rec['verification_citation_url'])
    blk = dict(schema_version='3.0.0', block_type='IMAGE_DATA_BLOCK', unit_system='SI_MILLIMETERS_AND_GRAMS',
               master_variant=rec['block_type'], temporal_and_dedup_anchor=anchor, subject_identity={'primary_name': rec['subject']})
    blk[fam] = spec
    # render priors are added by the loader as labelled MODELED templates; stand-ins here
    blk['integument_and_subsurface_physics' if organic else 'pbr_material_and_surface_physics'] = [{'material_id': 'M'}]
    blk['skeletal_rigging_and_3d_reconstruction_priors' if organic else 'structural_3d_hierarchy_and_mesh_priors'] = {'x': 1}
    blk['canonical_camera_and_lighting_baseline'] = {'reference_focal_length_mm': 50}
    validate_v3(blk)
    return key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--cat')
    ap.add_argument('--years', help='e.g. 2020-2026')
    ap.add_argument('--regions', help='e.g. 1-5 or 6-10')
    a = ap.parse_args()
    a.years = tuple(int(x) for x in a.years.split('-')) if a.years else None
    a.regions = range(int(a.regions.split('-')[0]), int(a.regions.split('-')[1]) + 1) if a.regions else None
    ok, bad, seen = 0, 0, set()
    with open(a.file, encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                print(f'line {n}: FAIL blank line'); bad += 1; continue
            try:
                rec = json.loads(line)
                if not isinstance(rec, dict):
                    raise ValueError('line is not a JSON object')
                key = check(rec, a)
                if key in seen:
                    raise ValueError('duplicate canonical_dedup_key')
                seen.add(key); ok += 1
            except Exception as e:  # report every failing line
                bad += 1
                print(f'line {n}: FAIL {e}')
    print(f'{a.file}: {ok} pass, {bad} fail')
    sys.exit(0 if ok and not bad else 1)


if __name__ == '__main__':
    main()
