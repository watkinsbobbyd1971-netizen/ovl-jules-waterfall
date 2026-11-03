# Taxonomy reconciliation guard — isolated draft

This standalone reporter changes no producer, loader, registry, database or existing record. It emits discrepancies to stdout. `eligible_for_independent_review` means metadata meets this contract, not that a fact is true, a block is sufficient, or a record should be applied. It cannot detect a fabricated statement disguised as observed evidence. Source verification, domain applicability and database reconciliation remain independent checks.

## Observed reason for the guard

Pinned baseline: `14c3e65de72619408054e2cf22cfc75e7592c261` in `watkinsbobbyd1971-netizen/ovl-jules-waterfall`.

| Source | Discrepancy |
| --- | --- |
| `FLEET_BLACKBOARD.json` vs `tools/validate_jules_batch.py` | REG_05 means Middle East & North Africa vs East Asia; REG_08 means East Asia vs Sub-Saharan Africa. Both use schema version 3.0.0. A schema version is not a taxonomy identity. |
| `tools/validate_jules_batch.py` | Category number >=11 selects organic morphology; this includes rocks, terrain and weather. The current `era_for` assigns all years <=2019 to ERA_06. |
| `direct_jev_waterfall.py` | Choice lists omit category definitions/version and missing answers become CAT_01/REG_01/ERA_07. |
| `antigravity_infinite_worker.py` | Missing category becomes row-index modulo20; each input expands to ten regions, era cycles by index and missing year is synthetic. This is code behavior evidence, not proof of the extent of database contamination. |

Issue308 owns compiler repair and issue309/PR313 owns dispatch repair. This change touches neither; these three files are new. No live repair claim is made.

## Explicit input contract

Registry object: `registry_id`, `taxonomy_version`, `source_reference`, and `categories`, `regions`, `eras` dictionaries keyed by code. Every entry has `semantic_id`, `label`, `definition`. Category entries also declare `allowed_variants`; no numeric threshold chooses organic or man-made. The registry hash is SHA256 of the entire supplied registry serialized with sorted keys, compact separators, UTF-8, no ASCII escaping or nonfinite numbers. A caller must select the authoritative registry separately; a hash proves consistency, not authority.

Record object: original `canonical_dedup_key`, `master_variant`, `taxonomy_binding` containing exact registry id/version/hash, and `classifications.category`, `.region`, `.era`. Each classification contains code, semantic_id, label and evidence. Evidence requires kind (`observed` or `explicitly_derived`), source_reference, source_record_id, supporting_evidence and retrieved_utc. Explicit derivations require a derivation description. Retrieval time and source fields are structural strings here; semantic/timestamp verification is a separate source audit. The reporter does not infer region from an account, year from row order, or subject identity from classification.

Unknown/absent/ambiguous bindings, codes, meanings, legacy top-level code disagreements, inappropriate variants and unsupported evidence kinds remain `unresolved`, with original record preserved. Duplicate JSON keys and nonfinite JSON numbers are rejected. Missing model responses never receive defaults. `compare_registries` produces a dry discrepancy report, including same-version/different-content conflicts, without choosing either registry.

## Identity and coverage migration proposal (not a registry)

The future canonical subject identifier should be stable and independent of category, region and year. Keep existing keys as aliases; do not rewrite keys or merge subjects merely because labels change. Migration needs a reviewed old-registry-id/version/code to new semantic-id crosswalk, explicit one-to-many ambiguity handling, before/after distinct-subject counts, source lineage and rollback evidence. This reporter does not perform a migration.

Use hierarchical parent/subtype facets so coverage is extensible. Transportation may include human-powered, animal-powered, motorized road, rail, maritime/submersible, airborne and spacecraft subtypes, with function, propulsion, era and region as separate facets. These are design examples, not approved mappings. Foods, manufactured goods, natural entities, events and abstract concepts require explicit applicability policies. Do not demand a positive mass or physical bounding box for an event or for an unavailable measurement. Unknown and not-applicable are distinct, evidenced states. The guard deliberately imposes no measurement requirement.

## Use and tests

`python3 tools/taxonomy_guard.py --registry reviewed-registry.json --records staged.jsonl`

Input files are read-only; JSONL reports go to stdout with original record and reason codes, followed by counts. Exit0 means all nonempty input records are eligible for independent metadata review; exit1 means unresolved or empty input; exit2 means blocked input/registry. Applied count is always zero. Report output may contain corpus content and must remain on approved private surfaces.

`python3 -m unittest discover -s tests -p test_taxonomy_guard.py -v`

Fixtures are explicitly synthetic and must never enter production. No registry file is shipped because authoritative meanings are still being reconciled. Before any integration: independent code review, verified authoritative registry, representative legacy snapshots, disagreement disposition, source validation, designation of a single writer, dry-run accounting and bounded reversible staging. Healthy production remains untouched.
