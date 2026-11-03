# Property-gap inspector: offline draft

This standalone prototype checks assertion metadata and produces a missing-property/review queue. It neither researches facts nor writes to BigQuery. It is not a factual validator, production migration, canonical taxonomy, trusted review service, or completion counter. All numerical fixtures and reviewer/source records in the tests are synthetic.

## Existing model and scope

The observed [schema snapshot](https://drive.google.com/file/d/1f5i1PheRZy_xxes3X5gA1EBAenTSxc-f/view), recorded at 14:36:47Z, lists ten control fields in `fill_ledger`: canonical_dedup_key, lane, source_library, assigned_worker, status, filled_from, fill_table, updated_at, created_at, origin. Its separate `fill_stage` includes subject identity, classifications, four measurements, basis and citation. These are operational/staging structures, not proof that a subject has only nine factual properties.

The [SQL artifact](https://drive.google.com/file/d/1r3P_A931KUJmm01EtrNWhS6bYT-Ob4ZR/view) lists nine top-level `blocks` insert fields, including a nested JSON block. Existing `research_facts` already holds subject_key, entity_id, source_library, property, value_num, value_text, unit, raw_value, source_url, researched_by and researched_at. This proposal extends/version-binds that model; it does not introduce a competing fact store. Preserve old keys and raw payloads. A `(subject_key, property)` anti-join alone suppresses alternate contexts, sources and conflicts. Proposed assertion identity includes subject, property, context, source/version, value and unit. The prototype reports fingerprints but performs no merge or claim operation.

The [master block SOT](https://docs.google.com/document/d/1XGfmUo1ZZ7Rp3zjK2nQsXBidCwNju4QvPM9Y57ZT1yI/edit) has distinct dimensional and morphometric families. Numeric category membership cannot determine applicability. Generic dry mass cannot replace adult biological mass, operating mass, food portion mass or weather observations.

## Input and queue contract

An individual-subject identity is stable independently of taxonomy, region and year. Broad class/make rows require resolution first. A subject selects an explicit versioned, hashed profile. Profiles supply property definitions, types, exact units, bounds, required context keys and optional evidence-backed conditions. Production profile authority is outside this module. Fixtures illustrate biology, equipment, event and prepared-food profiles; they do not establish canonical requirements.

Assertions are lists, never first-wins maps. Each has a distinct assertion ID, property, value/unit, context, data kind, status, producer and evidence. Evidence binds the exact subject/property/context/value and records source ID/version, locator, supporting text and retrieval time. Required context must match exactly; no automatic unit conversion or guessed applicability occurs.

Statuses remain distinct: absent, unresearched, unavailable, not_applicable, conflict, verified and derived. Unknown applicability queues research. A reviewed false condition cannot hide existing assertions. Unavailable and not-applicable assertions require evidence and explicit disposition; they do not become success by relabeling. Extra properties and original objects remain preserved.

Observed verified assertions require sourced_assertion data kind. Derived assertions require derived_assertion, a method and input IDs. Only reviewed, nonconflicting observed inputs are eligible in this version; chained derivations are unsupported. Divergent candidate values remain conflicts. No arithmetic derivation is performed or independently checked by this module.

Independent review metadata binds a digest of the immutable assertion, subject and full profile binding. Changes to values, sources, contexts, status, derivation or profile invalidate that digest. Conditional proofs bind subject/key/value/profile too. This is a consistency check, **not authentication**: a caller can fabricate review metadata or recompute a hash. Deployment requires separately trusted immutable review records and reviewer authorization. Nonempty source text does not prove that the source exists or supports the claim.

`extract_candidates` accepts explicit source paths and retains original raw values as unresearched inherited candidates. It never maps ambiguous wingspan fields to height, substitutes defaults, or treats uncited legacy values as reviewed facts. Split tractor dimension/mass and deer range fixtures are shape-only simulations.

## Source-informed profile design

- [Darwin Core](https://dwc.tdwg.org/list/) distinguishes measurement type, value, unit, method, accuracy, sex and life stage. A deer mass assertion needs specimen/population scope and statistic; a species-wide scalar is not assumed.
- [Deere shipping/machine weights](http://manuals.deere.com/omview/OMSJ10117_19/SH20560_00004A8_19_01JAN09_1.htm) depend on configuration and fluids. [Unballasted weights](http://manuals.deere.com/omview/OMAR188670_19/JO51195_0000017_19_22MAR05_1.htm) may include full fuel. Neither is automatically dry mass.
- [SOSA/SSN](https://www.w3.org/TR/vocab-ssn/) distinguishes observed property, feature, procedure, phenomenon time and result time. Weather observations do not require object dimensions.
- [USDA Foundation Foods](https://fdc.nal.usda.gov/docs/Foundation%5FFoods%5FDocumentation%5FApr2024.pdf) distinguishes edible portion, preparation and per-100g nutrient values. Recipe/portion/context must accompany food values.
- [JSON Schema conditionals](https://json-schema.org/understanding-json-schema/reference/conditionals) provide a production schema mechanism; this minimal Python prototype does not implement the full specification.

These inform local design choices, not a claim that the standards mandate every fixture field. The source research was supplied by the separate research lane; no numerical specimen or machine measurement is asserted here.

## Validation and limits

Run `python3 -m unittest discover -s tests -p 'test_property_gap_queue.py' -v` from the repository root. Tests cover context/source/profile binding, stale review, derived/observed separation, conditional conflicts, conflict propagation into derivations, missing fields, units, nonfinite numbers, legacy shape preservation and class-level identity rejection.

Malformed input/profile structures can raise ValueError; the caller must quarantine failures. This prototype supports scalar numeric/text properties only; ranges remain candidate payloads until an explicit range profile is implemented. No network calls, source verification, database performance tests, production writes, exports, scheduling, or trusted-review authentication are included. Production integration requires independent review, authoritative profiles, compatibility/version strategy, idempotent writer and claims integration, and a read-only corpus dry run before any separately authorized deployment.
