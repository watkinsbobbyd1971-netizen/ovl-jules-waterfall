# CORPUS-RULES.md: read this first. Where it differs from AGENTS.md, this file wins.

Files that break these rules are thrown away whole, so a single bad habit loses the whole chunk. Nearly 90 percent of earlier rows were lost this way, mostly to the first two rules. A short, correct file is worth far more than a long one.

## Before you commit
Run `python3 check_output.py out/<category>/chunk-NNNN.csv`, and fix or remove rows until it prints READY and exits 0. `--fix` corrects value form and removes every row that still fails; then run it again without `--fix`. Don't commit a file that isn't READY, and don't edit the script. Commit only your output file, and its notes file if it's empty.

## Rules
1. **One source URL per entity.** `source_url` names the one record the value came from: `https://www.wikidata.org/wiki/Q42`, `https://api.gbif.org/v1/species/212`, one museum object's page or API record. Fetch in bulk by SPARQL or API if you like, but never cite the query. No SPARQL or API query URLs, search pages, list pages, `List_of` or `Category:` pages, or home pages. Never build or guess a URL: cite one you actually fetched.
2. **One value per key and column.** At most one row for each `canonical_dedup_key` and `column_name` pair. If sources disagree, or a thing has several values and you can't tell which the column means, leave the cell out.
3. **JSON scalars of the column's type.** A `value types: string` column takes a JSON string, with quotes: `"Apollo 11"`. A `value types: number` column takes a bare JSON number in the unit COLUMNS.csv gives: `1250.5`, never `"1250.5"` or `1250.5 mm`. Convert units only by exact formula.
4. **No arrays.** No multi-item arrays and no one-item arrays. If several values apply and you can't choose one, leave the cell out.
5. **One entity per key.** All of a key's rows cite the same entity. Never put one entity on two keys unless both keys name that same thing.
6. **Exact name and class check.** Before writing a row, check that the entity's name matches `subject_name` and that it is the same kind of thing as this category: a ship for watercraft, a taxon for mammal. A shared name isn't a match: *Apollo* the spacecraft, the god and the theatre are different entities. If you can't tell, skip the subject.
7. **Height is never `dimension_length`.** That column means length only. A height, width, diameter, depth or thickness goes nowhere, so leave it out. A building's height isn't its length.
8. **Empty beats a guess.** No estimates, averages, typical values, values for a similar thing, or placeholders such as `unknown`. A subject with nothing sourced simply has no rows. An empty file with a notes file is a valid result.
9. **Skip what bulk already has.** Never fill a column named in SKIP_COLUMNS.txt on this branch: open data joins already cover it. Spend your effort on the other columns in COLUMNS.csv, above all real measurements.
