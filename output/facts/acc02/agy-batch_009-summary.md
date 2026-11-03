# acc02 Batch 009 Research Summary (`agy-batch_009`)

- **Job**: `J-20261101-CORPUS-AUTO` (`COORD-004` / `ASSIGN-TABLE-v2.md`)
- **Worker**: `agy` (replacing rate-limited Jules session `1219466549110971038`)
- **Manifest**: `ledger_slices/acc02/acc02_batch_009_jules-1219466549110971038.csv`
- **Output Facts**: `output/facts/acc02/agy-batch_009.jsonl`

## Key & Fact Counts

| Metric | Count |
|---|---|
| Total keys researched | 100 |
| Keys resolved to exact Wikidata QID (`LIB40`–`LIB43`) | 92 |
| Keys in `LIB39-GETTY-AAT` (vocabulary concepts; no physical dims/mass) | 8 |
| Keys with ≥1 sourced fact (dimensions, mass, material, or year) | 32 |
| Keys with sourced physical dimensions (`*_mm` / `area_m2`) or `mass_g` | 9 |
| Keys with `no_source` recorded for unavailable dimensions/mass | 91 |
| Total JSONL lines written | 140 |
| Sourced fact lines (`height_mm`, `width_mm`, `length_mm`, `diameter_mm`, `depth_mm`, `thickness_mm`, `mass_g`, `material`, `year`, etc.) | 49 |
| Unavailable fact lines (`property = "no_source"`) | 91 |

## Breakdown by Source Library

| Source Library | Keys |
|---|---|
| `LIB39-GETTY-AAT` | 8 |
| `LIB43-OBJECTS` | 92 |

## Breakdown by Property

| Property | Rows |
|---|---|
| `area_m2` | 3 |
| `diameter_mm` | 1 |
| `elevation_above_sea_level_mm` | 6 |
| `height_mm` | 2 |
| `length_mm` | 2 |
| `material` | 14 |
| `no_source` | 91 |
| `width_mm` | 3 |
| `year` | 18 |
