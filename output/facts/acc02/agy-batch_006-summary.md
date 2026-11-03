# acc02 Batch 006 Research Summary (`agy-batch_006`)

- **Job**: `J-20261101-CORPUS-AUTO` (`COORD-004` / `ASSIGN-TABLE-v2.md`)
- **Worker**: `agy` (replacing rate-limited Jules session `1138768997239189254`)
- **Manifest**: `ledger_slices/acc02/acc02_batch_006_jules-1138768997239189254.csv`
- **Output Facts**: `output/facts/acc02/agy-batch_006.jsonl`

## Key & Fact Counts

| Metric | Count |
|---|---|
| Total keys researched | 100 |
| Keys resolved to exact Wikidata QID (`LIB40`–`LIB43`) | 91 |
| Keys in `LIB39-GETTY-AAT` (vocabulary concepts; no physical dims/mass) | 9 |
| Keys with ≥1 sourced fact (dimensions, mass, material, or year) | 82 |
| Keys with sourced physical dimensions (`*_mm` / `area_m2`) or `mass_g` | 59 |
| Keys with `no_source` recorded for unavailable dimensions/mass | 41 |
| Total JSONL lines written | 292 |
| Sourced fact lines (`height_mm`, `width_mm`, `length_mm`, `diameter_mm`, `depth_mm`, `thickness_mm`, `mass_g`, `material`, `year`, etc.) | 251 |
| Unavailable fact lines (`property = "no_source"`) | 41 |

## Breakdown by Source Library

| Source Library | Keys |
|---|---|
| `LIB39-GETTY-AAT` | 9 |
| `LIB43-OBJECTS` | 91 |

## Breakdown by Property

| Property | Rows |
|---|---|
| `depth_mm` | 4 |
| `diameter_mm` | 9 |
| `height_mm` | 34 |
| `length_mm` | 23 |
| `mass_g` | 5 |
| `material` | 72 |
| `no_source` | 41 |
| `thickness_mm` | 5 |
| `width_mm` | 32 |
| `year` | 67 |
