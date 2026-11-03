# acc02 Batch 008 Research Summary (`agy-batch_008`)

- **Job**: `J-20261101-CORPUS-AUTO` (`COORD-004` / `ASSIGN-TABLE-v2.md`)
- **Worker**: `agy` (replacing rate-limited Jules session `11776217541142937478`)
- **Manifest**: `ledger_slices/acc02/acc02_batch_008_jules-11776217541142937478.csv`
- **Output Facts**: `output/facts/acc02/agy-batch_008.jsonl`

## Key & Fact Counts

| Metric | Count |
|---|---|
| Total keys researched | 100 |
| Keys resolved to exact Wikidata QID (`LIB40`–`LIB43`) | 90 |
| Keys in `LIB39-GETTY-AAT` (vocabulary concepts; no physical dims/mass) | 10 |
| Keys with ≥1 sourced fact (dimensions, mass, material, or year) | 80 |
| Keys with sourced physical dimensions (`*_mm` / `area_m2`) or `mass_g` | 63 |
| Keys with `no_source` recorded for unavailable dimensions/mass | 37 |
| Total JSONL lines written | 299 |
| Sourced fact lines (`height_mm`, `width_mm`, `length_mm`, `diameter_mm`, `depth_mm`, `thickness_mm`, `mass_g`, `material`, `year`, etc.) | 262 |
| Unavailable fact lines (`property = "no_source"`) | 37 |

## Breakdown by Source Library

| Source Library | Keys |
|---|---|
| `LIB39-GETTY-AAT` | 10 |
| `LIB43-OBJECTS` | 90 |

## Breakdown by Property

| Property | Rows |
|---|---|
| `depth_mm` | 11 |
| `diameter_mm` | 15 |
| `height_mm` | 49 |
| `length_mm` | 5 |
| `mass_g` | 1 |
| `material` | 76 |
| `no_source` | 37 |
| `thickness_mm` | 3 |
| `width_mm` | 23 |
| `year` | 79 |
