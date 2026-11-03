# Met ledger slices (J-20261101-CORPUS-AUTO waterfall)

Each file is one Jules session's slice of EXISTING corpus rows that need their measurements filled.
Do not create new subjects. Fill only these rows.

| File | Jules session |
|---|---|
| met_ACC_04_jules-17630918581046126614.csv | 17630918581046126614 |
| met_ACC_05_jules-7140849600672725366.csv | 7140849600672725366 |
| met_ACC_06_jules-10548457540368483641.csv | 10548457540368483641 |

Columns: canonical_dedup_key, entity_id, subject (Met title), description (medium, maker, date, culture), source_library, category_code.

## Research source
The Met Open Access dataset (CC0): https://github.com/metmuseum/openaccess (MetObjects.csv, "Dimensions" column).
Match each row to its Met object by title plus medium, date and culture from the description. Skip ambiguous matches.

## Output: facts, not blocks
Write `output/facts/met/<your-session-id>_partNN.jsonl`, one JSON object per line:

    {"canonical_dedup_key": "<from the slice>", "subject_key": "MET:<Object ID>", "property": "height_mm",
     "value_num": 123.4, "unit": "mm", "raw_value": "<original Dimensions text>",
     "source_url": "https://www.metmuseum.org/art/collection/search/<Object ID>"}

Properties: height_mm, width_mm, length_mm, depth_mm, diameter_mm, mass_g, material, year, culture, object_name.
Convert cm to mm (x10) and in to mm (x25.4). Write only values stated in the Met record; never estimate.
For a row with no match or no dimensions, write {"canonical_dedup_key": "...", "property": "no_source", "value_text": "<reason>"}.
A loader copies these facts into BigQuery image_corpus.research_facts. Gemini wave workers then fill the rows in place.
