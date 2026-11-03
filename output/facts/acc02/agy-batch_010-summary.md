# acc02 Batch 010 Research Summary (`agy-batch_010`)

- **Job**: `J-20261101-CORPUS-AUTO` (`COORD-004` / `ASSIGN-TABLE-v2.md`)
- **Worker**: `agy` (replacing rate-limited Jules session `12976717753041984957`)
- **Manifest**: `ledger_slices/acc02/acc02_batch_010_jules-12976717753041984957.csv`
- **Output Facts**: `output/facts/acc02/agy-batch_010.jsonl`

## Key & Fact Counts

| Metric | Count |
|---|---|
| Total keys researched | 100 |
| Keys resolved to exact Wikidata QID (`LIB40`–`LIB43`) | 82 |
| Keys in `LIB39-GETTY-AAT` (vocabulary concepts; no physical dims/mass) | 18 |
| Keys with ≥1 sourced fact (dimensions, mass, material, or year) | 42 |
| Keys with sourced physical dimensions (`*_mm` / `area_m2`) or `mass_g` | 24 |
| Keys with `no_source` recorded for unavailable dimensions/mass | 76 |
| Total JSONL lines written | 162 |
| Sourced fact lines (`height_mm`, `width_mm`, `length_mm`, `diameter_mm`, `depth_mm`, `thickness_mm`, `mass_g`, `material`, `year`, etc.) | 86 |
| Unavailable fact lines (`property = "no_source"`) | 76 |

## Breakdown by Source Library

| Source Library | Keys |
|---|---|
| `LIB39-GETTY-AAT` | 18 |
| `LIB43-OBJECTS` | 82 |

## Breakdown by Property

| Property | Rows |
|---|---|
| `area_m2` | 4 |
| `depth_mm` | 6 |
| `diameter_mm` | 5 |
| `draft_mm` | 1 |
| `elevation_above_sea_level_mm` | 4 |
| `height_mm` | 11 |
| `length_mm` | 5 |
| `mass_g` | 1 |
| `material` | 20 |
| `no_source` | 76 |
| `vertical_depth_mm` | 1 |
| `width_mm` | 10 |
| `year` | 18 |
