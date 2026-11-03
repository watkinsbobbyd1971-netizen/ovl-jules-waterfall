# acc02 Batch 005 Research Summary (`agy-batch_005`)

- **Job**: `J-20261101-CORPUS-AUTO` (`COORD-004` / `ASSIGN-TABLE-v2.md`)
- **Worker**: `agy` (replacing rate-limited Jules session `11341207145988416842`)
- **Manifest**: `ledger_slices/acc02/acc02_batch_005_jules-11341207145988416842.csv`
- **Output Facts**: `output/facts/acc02/agy-batch_005.jsonl`

## Key & Fact Counts

| Metric | Count |
|---|---|
| Total keys researched | 100 |
| Keys resolved to exact Wikidata QID (`LIB40`–`LIB43`) | 91 |
| Keys in `LIB39-GETTY-AAT` (vocabulary concepts; no physical dims/mass) | 9 |
| Keys with ≥1 sourced fact (dimensions, mass, material, or year) | 84 |
| Keys with sourced physical dimensions (`*_mm` / `area_m2`) or `mass_g` | 3 |
| Keys with `no_source` recorded for unavailable dimensions/mass | 97 |
| Total JSONL lines written | 187 |
| Sourced fact lines (`height_mm`, `width_mm`, `length_mm`, `diameter_mm`, `depth_mm`, `thickness_mm`, `mass_g`, `material`, `year`, etc.) | 90 |
| Unavailable fact lines (`property = "no_source"`) | 97 |

## Breakdown by Source Library

| Source Library | Keys |
|---|---|
| `LIB39-GETTY-AAT` | 9 |
| `LIB42-HISTORY` | 87 |
| `LIB43-OBJECTS` | 4 |

## Breakdown by Property

| Property | Rows |
|---|---|
| `diameter_mm` | 1 |
| `height_mm` | 2 |
| `material` | 4 |
| `no_source` | 97 |
| `width_mm` | 2 |
| `year` | 81 |
