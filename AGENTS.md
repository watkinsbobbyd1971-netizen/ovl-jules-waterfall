# AGENTS.md - corpus property fill (read fully, ask nothing)
Task: fill empty property columns for the subjects in tasks/<category>/chunk-NNNN.csv.gz (columns canonical_dedup_key,subject_name) using ONLY real, sourced values.
Allowed columns for the category: COLUMNS.csv (column_name,data_type,unit,description).
Rules:
1. Real values only. No estimates, averages, defaults, hash-generated or invented values. A value with no source stays out of the file.
2. Prefer bulk structured sources fetched by script: Wikidata (SPARQL/entity API), museum open APIs (Met, Smithsonian, Europeana, Rijksmuseum, Cleveland, Art Institute of Chicago), GBIF, Open Tree of Life, USGS/NASA/NOAA open data, other public datasets. Match subjects by exact name or identifier; skip ambiguous matches.
3. Respect each column's data_type and unit (convert units only by exact formula).
4. Never touch BigQuery, Google Drive, gcloud or any credentials. Do not modify this file, tasks/ or COLUMNS.csv.
5. Output: out/<category>/chunk-NNNN.csv with header exactly `canonical_dedup_key,column_name,value,source_url`; one row per sourced value; source_url is the exact page/API URL the value came from. Commit only that file. An empty result is a valid result: commit the header only plus out/<category>/chunk-NNNN.notes.txt saying which sources you tried.
6. Do not ask questions; finish and submit.
