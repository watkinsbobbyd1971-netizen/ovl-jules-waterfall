# acc02 Batch 002 Research Summary (`agy-batch_002`)

- **Job**: `J-20261101-CORPUS-AUTO` (`COORD-004` / `ASSIGN-TABLE-v2.md`)
- **Worker**: `agy` (replacing rate-limited Jules session `10274141118200915599`)
- **Manifest**: `ledger_slices/acc02/acc02_batch_002_jules-10274141118200915599.csv`
- **Output Facts**: `output/facts/acc02/agy-batch_002.jsonl`

## Key & Fact Counts

| Metric | Count |
|---|---|
| Total keys researched | 100 |
| Keys resolved to exact Wikidata QID (`LIB40`–`LIB43`) | 36 |
| Keys in `LIB39-GETTY-AAT` (vocabulary concepts; no physical dims/mass) | 64 |
| Keys with ≥1 sourced fact (dimensions, mass, material, or year) | 8 |
| Keys with sourced physical dimensions (`*_mm` / `area_m2`) or `mass_g` | 0 |
| Keys with `no_source` recorded for unavailable dimensions/mass | 100 |
| Total JSONL lines written | 108 |
| Sourced fact lines (`height_mm`, `width_mm`, `length_mm`, `diameter_mm`, `depth_mm`, `thickness_mm`, `mass_g`, `material`, `year`, etc.) | 8 |
| Unavailable fact lines (`property = "no_source"`) | 100 |

## Breakdown by Source Library

| Source Library | Keys |
|---|---|
| `LIB39-GETTY-AAT` | 64 |
| `LIB40-BELIEF` | 36 |

## Breakdown by Property

| Property | Rows |
|---|---|
| `no_source` | 100 |
| `year` | 8 |
