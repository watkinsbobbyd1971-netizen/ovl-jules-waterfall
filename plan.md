1. Write Python script `run.py` to query Wikidata API for entities matching subject_name in `tasks/electronics/chunk-0013.csv.gz`.
2. Extract claims matching columns `component_relationship` (P527), `descriptive_identity` (P31, P279), `dimension_length` (P2043), `manufacturer_or_creator` (P176, P170), `mass` (P2067), `material_identity` (P186), and `rated_power` (P2102).
3. Execute the script to create `out/electronics/chunk-0013.csv` and `out/electronics/chunk-0013.notes.txt`.
4. Verify the output files are correctly formatted and contain the extracted data.
5. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
6. Commit the output files and submit the branch.
