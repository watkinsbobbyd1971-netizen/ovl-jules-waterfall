1. Write a Python script to fetch the property values for the subjects from Wikidata.
    - I'll map Wikidata properties to columns allowed in `built_environment` (descriptive_identity -> P31, location -> P625, construction_date -> P571 or P1619, creator_or_attribution -> P84, material_identity -> P186, component_relationship -> P527).
    - Read `tasks/built_environment/chunk-0018.csv.gz` and extract `canonical_dedup_key` and `subject_name`.
    - Batch query Wikidata with SPARQL (`VALUES ?itemLabel { ... }`) to avoid hitting limits.
    - Write exact matches and sourced values to `out/built_environment/chunk-0018.csv` in `canonical_dedup_key,column_name,value,source_url` format, properly quoting items if needed.
2. Execute the script to generate `out/built_environment/chunk-0018.csv` and `out/built_environment/chunk-0018.notes.txt`.
3. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
4. Add the generated CSV and submit it.
