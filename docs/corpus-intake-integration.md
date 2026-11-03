# Paused-production compiler repair

This replaces the actual Jules compiler and Antigravity daemon entry paths with review staging through the taxonomy guard from PR314 and property-gap inspector from PR315. It does not activate production. Issue308's Jules task17168685733885511280 reported an error; the Operator authorized this isolated takeover. Existing instructions, workflows, account settings, corpus outputs and database are untouched.

## Behavior

Both entrypoints read only `batches/profile-N/batch_XX.csv`. Broad shared-file fallback is rejected because it did not prove profile ownership and enabled repeated compilation of queue01 under different batch names. The caller must supply an explicitly claimed profile partition. Preserve existing CSVs; do not copy one batch into several filenames to inflate output.

The adapter retains every raw row. Legacy rows without the explicit contract produce `needs_research` reports, never guessed category, region, era, year, citation, PBR material or measurements. Malformed envelopes, duplicate keys (all copies), inconsistent source identity, ragged CSV and unbound properties are held. No JSON structure or hash is described as factual validation.

CSV envelope columns are `canonical_dedup_key` (or legacy `dedup_key`), stable `subject_id`, `taxonomy_record_json`, and `property_subject_json`. The taxonomy record must bind the same stable subject and legacy key. Any supplied top-level category/region/era/variant must agree. The nested property subject follows PR315. CLI options `--registry registry.json --profiles profiles.json` select explicit registry/profile objects. Profiles are a map keyed by their own profile ID. Missing contracts hold rows; malformed contracts produce nonzero errors.

Registry metadata must say `authority_state: approved` and each used axis entry `status: approved`; proposals/unresolved mappings are held. This is an explicit metadata boundary, not trusted authentication. Proposed property profiles remain review-only. Category-to-profile semantic approval and a trusted authority/reviewer service are still required before production. No record reaches an applied or source-validated state in this staging path even when all metadata checks succeed.

Reports are under `review-output/`, outside existing loader `output/` paths, with `.review-<hash>.jsonl` names. Names bind resolved source path, the exact source bytes parsed, and registry/profile content. Existing identical reports are reused; changed source/contract gets a new report. Different existing report content is never overwritten. The source cannot also be the output. A mid-write crash leaves a partial report that must be reconciled, not silently replaced.

Counts distinguish input rows, staged review reports, eligible-for-independent-review rows, and needs-research rows. Applied and source-validated are always zero. `--apply` returns exit2 without invoking BigQuery. The old daemon's ignored load errors and misleading pushed count are removed. The designated database writer remains separately owned; this repair does not implement or claim exactly-once application.

## CLI and compatibility

`OVL_PROFILE=1 python3 jules_waterfall_worker.py 1 --registry registry.json --profiles profiles.json`

`python3 antigravity_autonomous_daemon.py --profile 1 --once --registry registry.json --profiles profiles.json`

`python3 antigravity_autonomous_daemon.py --profile 1 --loop --max-rounds 2 --poll-seconds 5 --registry registry.json --profiles profiles.json`

Exit0 means a nonempty input set produced no held rows, **not** factual acceptance or application. Exit1 means held/missing work; exit2 means blocked input/contract/application; interruption is130. The daemon defaults to one round. Loop rounds are explicitly bounded1..1000. `--workers` is accepted for compatibility but this review path is sequential. `--profile all`, shared input fallback and direct loads are intentionally unsupported. `compile_csv_to_jsonl` now returns a structured count report instead of an integer; callers must consume explicit stage counters.

No automatic migration is attempted. Unchanged report reuse is resumable review staging, not a durable applied checkpoint. A source/registry/schema change requires new review. External trusted review records, authoritative category/profile reconciliation, idempotent designated writer, and independent end-to-end review are dependencies for any later production activation.

## Checks

`python3 -m unittest discover -s tests -v`

Tests combine the prior isolated guard suites with real-entrypoint regressions for raw source preservation, absent contracts, subject mismatch, duplicate/ragged inputs, profile isolation, same-basename inputs, source/contract-version preservation, bounded loop, and blocked application. All facts/authorities in fixtures are synthetic. No network/database loads occur.
