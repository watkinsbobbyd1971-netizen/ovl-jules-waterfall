# acc02 Batch 003 Research Summary (`agy-batch_003`)

- **Job**: `J-20261101-CORPUS-AUTO` (`COORD-004` / `ASSIGN-TABLE-v2.md`)
- **Worker**: `agy` (replacing rate-limited Jules session `10815999474767519177`)
- **Manifest**: `ledger_slices/acc02/acc02_batch_003_jules-10815999474767519177.csv`
- **Output Facts**: `output/facts/acc02/agy-batch_003.jsonl`

## Key & Fact Counts

| Metric | Count |
|---|---|
| Total keys researched | 100 |
| Keys resolved to exact Wikidata QID (`LIB40`–`LIB43`) | 91 |
| Keys in `LIB39-GETTY-AAT` (vocabulary concepts; no physical dims/mass) | 9 |
| Keys with ≥1 sourced fact (dimensions, mass, material, or year) | 35 |
| Keys with sourced physical dimensions (`*_mm` / `area_m2`) or `mass_g` | 1 |
| Keys with `no_source` recorded for unavailable dimensions/mass | 99 |
| Total JSONL lines written | 135 |
| Sourced fact lines (`height_mm`, `width_mm`, `length_mm`, `diameter_mm`, `depth_mm`, `thickness_mm`, `mass_g`, `material`, `year`, etc.) | 36 |
| Unavailable fact lines (`property = "no_source"`) | 99 |

## Breakdown by Source Library

| Source Library | Keys |
|---|---|
| `LIB39-GETTY-AAT` | 9 |
| `LIB40-BELIEF` | 71 |
| `LIB41-PERFORMING-ARTS` | 20 |

## Breakdown by Property

| Property | Rows |
|---|---|
| `height_mm` | 1 |
| `material` | 1 |
| `no_source` | 99 |
| `year` | 34 |
