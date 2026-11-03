# acc02 Batch 007 Research Summary (`agy-batch_007`)

- **Job**: `J-20261101-CORPUS-AUTO` (`COORD-004` / `ASSIGN-TABLE-v2.md`)
- **Worker**: `agy` (replacing rate-limited Jules session `11460984863184486419`)
- **Manifest**: `ledger_slices/acc02/acc02_batch_007_jules-11460984863184486419.csv`
- **Output Facts**: `output/facts/acc02/agy-batch_007.jsonl`

## Key & Fact Counts

| Metric | Count |
|---|---|
| Total keys researched | 100 |
| Keys resolved to exact Wikidata QID (`LIB40`–`LIB43`) | 91 |
| Keys in `LIB39-GETTY-AAT` (vocabulary concepts; no physical dims/mass) | 9 |
| Keys with ≥1 sourced fact (dimensions, mass, material, or year) | 73 |
| Keys with sourced physical dimensions (`*_mm` / `area_m2`) or `mass_g` | 38 |
| Keys with `no_source` recorded for unavailable dimensions/mass | 62 |
| Total JSONL lines written | 220 |
| Sourced fact lines (`height_mm`, `width_mm`, `length_mm`, `diameter_mm`, `depth_mm`, `thickness_mm`, `mass_g`, `material`, `year`, etc.) | 158 |
| Unavailable fact lines (`property = "no_source"`) | 62 |

## Breakdown by Source Library

| Source Library | Keys |
|---|---|
| `LIB39-GETTY-AAT` | 9 |
| `LIB43-OBJECTS` | 91 |

## Breakdown by Property

| Property | Rows |
|---|---|
| `area_m2` | 2 |
| `depth_mm` | 3 |
| `diameter_mm` | 6 |
| `elevation_above_sea_level_mm` | 2 |
| `height_mm` | 22 |
| `length_mm` | 17 |
| `mass_g` | 1 |
| `material` | 47 |
| `no_source` | 62 |
| `thickness_mm` | 1 |
| `width_mm` | 17 |
| `year` | 40 |
