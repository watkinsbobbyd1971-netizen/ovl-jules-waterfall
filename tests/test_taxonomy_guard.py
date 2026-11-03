import contextlib
import copy
import io
import json
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from taxonomy_guard import inspect_record, validate_registry, compare_registries, strict_json, main


def fixture():
    # Deliberately synthetic fixtures: not a proposed OVL taxonomy.
    reg = {"registry_id": "test-only", "taxonomy_version": "fixture-1", "source_reference": "fixture://registry"}
    for table, code in (("categories", "CAT_19"), ("regions", "REG_05"), ("eras", "ERA_TEST")):
        reg[table] = {code: {"semantic_id": "fixture:" + table, "label": "Test " + table,
                             "definition": "Test-only explicit meaning"}}
    reg["categories"]["CAT_19"]["allowed_variants"] = ["TEST_NONPHYSICAL"]
    row = {"canonical_dedup_key": "stable-subject-1", "master_variant": "TEST_NONPHYSICAL",
           "taxonomy_binding": validate_registry(reg), "classifications": {}}
    for axis, table in (("category", "categories"), ("region", "regions"), ("era", "eras")):
        code, entry = next(iter(reg[table].items()))
        row["classifications"][axis] = {"code": code, "semantic_id": entry["semantic_id"], "label": entry["label"],
            "evidence": {"kind": "observed", "source_reference": "fixture://source", "source_record_id": "subject-1",
                         "supporting_evidence": "Test statement only", "retrieved_utc": "2026-11-03T00:00:00Z"}}
    return reg, row


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.reg, self.row = fixture()

    def reject(self):
        self.assertEqual(inspect_record(self.row, self.reg)["state"], "unresolved")

    def test_nonphysical_needs_no_fabricated_measurement(self):
        self.assertEqual(inspect_record(self.row, self.reg)["state"], "eligible_for_independent_review")

    def test_original_unchanged(self):
        before = copy.deepcopy(self.row)
        inspect_record(self.row, self.reg)
        self.assertEqual(before, self.row)

    def test_missing_binding_not_schema_version_substitute(self):
        del self.row["taxonomy_binding"]
        self.row["schema_version"] = "3.0.0"
        self.reject()

    def test_same_version_changed_meaning_hash_rejected(self):
        self.reg["regions"]["REG_05"]["label"] = "Different region"
        self.reject()

    def test_wrong_namespace_rejected(self):
        self.row["taxonomy_binding"]["registry_id"] = "another-registry"
        self.reject()

    def test_known_code_wrong_meaning(self):
        self.row["classifications"]["region"]["semantic_id"] = "wrong"
        self.reject()

    def test_unknown_category(self):
        self.row["classifications"]["category"]["code"] = "CAT_99"
        self.reject()

    def test_missing_model_answer_not_defaulted(self):
        del self.row["classifications"]["era"]
        result = inspect_record(self.row, self.reg)
        self.assertIn("era:missing_classification", result["reasons"])
        self.assertNotIn("era", result["original"]["classifications"])

    def test_legacy_disagreement_no_rewrite(self):
        self.row["region_code"] = "REG_08"
        self.reject()
        self.assertEqual(self.row["region_code"], "REG_08")

    def test_nested_v3_region_label_conflict(self):
        self.row["temporal_and_dedup_anchor"] = {"region_code": "REG_05", "region_name": "Middle East & North Africa"}
        self.reject()

    def test_nested_identity_conflict(self):
        self.row["temporal_and_dedup_anchor"] = {"canonical_dedup_key": "different-subject"}
        self.reject()

    def test_top_level_category_label_conflict(self):
        self.row["category_name"] = "Vehicles"
        self.reject()

    def test_nested_v3_category_code_conflict(self):
        self.row["temporal_and_dedup_anchor"] = {"category_code": "CAT_15", "category_name": "Insects"}
        self.reject()

    def test_fixture_minerals_and_events_not_organic_by_number(self):
        for code, label in (("CAT_18", "Fixture minerals"), ("CAT_20", "Fixture events")):
            reg, row = fixture()
            reg["categories"] = {code: {"semantic_id": "fixture:" + code, "label": label,
                "definition": "Test-only meaning, not authority", "allowed_variants": ["TEST_NONPHYSICAL"]}}
            row["taxonomy_binding"] = validate_registry(reg)
            row["classifications"]["category"].update(code=code, semantic_id="fixture:"+code, label=label)
            self.assertEqual(inspect_record(row, reg)["state"], "eligible_for_independent_review")

    def test_fixture_cat15_vehicle_does_not_become_insect(self):
        reg, row = fixture()
        reg["categories"] = {"CAT_15": {"semantic_id": "fixture:insects", "label": "Fixture insects",
            "definition": "Test only", "allowed_variants": ["TEST_ORGANIC"]}}
        row["taxonomy_binding"] = validate_registry(reg)
        row["classifications"]["category"].update(code="CAT_15", semantic_id="fixture:vehicles", label="Fixture vehicles")
        self.assertEqual(inspect_record(row, reg)["state"], "unresolved")

    def test_synthetic_modulo_evidence_rejected(self):
        self.row["classifications"]["era"]["evidence"]["kind"] = "row_index_modulo"
        self.reject()

    def test_url_alone_insufficient(self):
        self.row["classifications"]["category"]["evidence"] = {"source_reference": "https://example.org"}
        self.reject()

    def test_derivation_requires_explicit_method(self):
        self.row["classifications"]["era"]["evidence"]["kind"] = "explicitly_derived"
        self.reject()

    def test_category_number_does_not_select_variant(self):
        self.row["master_variant"] = "ORGANIC_MASTER"
        self.reject()

    def test_registry_missing_definitions_blocked(self):
        del self.reg["categories"]["CAT_19"]["definition"]
        with self.assertRaises(ValueError): validate_registry(self.reg)

    def test_registry_same_version_conflicts_reported(self):
        other = copy.deepcopy(self.reg)
        other["regions"]["REG_05"]["label"] = "Changed meaning"
        result = compare_registries(self.reg, other)
        self.assertTrue(result["same_version_different_content"])
        self.assertEqual(result["differences"][0]["code"], "REG_05")

    def test_ambiguous_json_rejected(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}'):
            with self.assertRaises(ValueError): strict_json(text)

    def test_cli_duplicate_and_malformed_continue_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry, records = pathlib.Path(tmp)/"registry.json", pathlib.Path(tmp)/"records.jsonl"
            registry.write_text(json.dumps(self.reg))
            raw = json.dumps(self.row) + "\n" + json.dumps(self.row) + "\n{broken\n"
            records.write_text(raw)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["--registry", str(registry), "--records", str(records)])
            self.assertEqual(result, 1)
            self.assertEqual(records.read_text(), raw)
            summary = json.loads(output.getvalue().splitlines()[-1])["summary"]
            self.assertEqual(summary, {"records": 3, "unresolved": 2, "eligible_for_independent_review": 1, "applied": 0})


if __name__ == "__main__": unittest.main()
