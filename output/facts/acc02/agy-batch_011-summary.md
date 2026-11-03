# acc02 Batch 011 Research Summary (`agy-batch_011`)

- **Job**: `J-20261101-CORPUS-AUTO` (`COORD-004` / `ASSIGN-TABLE-v2.md`)
- **Worker**: `agy` (replacing rate-limited Jules session `14330237360221711114`)
- **Manifest**: `ledger_slices/acc02/acc02_batch_011_jules-14330237360221711114.csv`
- **Output Facts**: `output/facts/acc02/agy-batch_011.jsonl`

## Key & Fact Counts

| Metric | Count |
|---|---|
| Total keys researched | 100 |
| Keys resolved to exact Wikidata QID (`LIB40`–`LIB43`) | 28 |
| Keys in `LIB39-GETTY-AAT` (vocabulary concepts; no physical dims/mass) | 72 |
| Keys with ≥1 sourced fact (dimensions, mass, material, or year) | 14 |
| Keys with sourced physical dimensions (`*_mm` / `area_m2`) or `mass_g` | 10 |
| Keys with `no_source` recorded for unavailable dimensions/mass | 90 |
| Total JSONL lines written | 126 |
| Sourced fact lines (`height_mm`, `width_mm`, `length_mm`, `diameter_mm`, `depth_mm`, `thickness_mm`, `mass_g`, `material`, `year`, etc.) | 36 |
| Unavailable fact lines (`property = "no_source"`) | 90 |

## Breakdown by Source Library

| Source Library | Keys |
|---|---|
| `LIB39-GETTY-AAT` | 72 |
| `LIB43-OBJECTS` | 28 |

## Breakdown by Property

| Property | Rows |
|---|---|
| `area_m2` | 3 |
| `height_mm` | 3 |
| `length_mm` | 5 |
| `mass_g` | 1 |
| `material` | 10 |
| `no_source` | 90 |
| `thickness_mm` | 1 |
| `vertical_depth_mm` | 1 |
| `width_mm` | 4 |
| `year` | 8 |
