import copy
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from property_gap_queue import inspect_subject, profile_binding, extract_candidates, review_digest


def reviewed(item, subject):
    item["independent_review"]["reviewed_digest"] = review_digest(item, subject["subject_id"], subject["profile_binding"])


def fixture(kind="deer"):
    # Values, identifiers and evidence are fabricated TEST FIXTURES, not corpus data.
    specs = {
        "deer": ("body_mass", "g", {"sex": "female", "life_stage": "adult", "statistic": "individual",
                 "population": "test population", "measurement_time": "test instant", "method": "test scale"}),
        "tractor": ("operating_mass", "g", {"model": "test tractor", "model_year": "test year",
                    "configuration": "test cab/MFWD", "mass_basis": "operating_full_fluids"}),
        "weather": ("precipitation_depth", "mm", {"feature": "test station", "phenomenon_time": "test interval",
                    "result_time": "test result instant", "procedure": "test gauge", "statistic": "interval_total"}),
        "prepared_food": ("energy_per_100g", "kJ", {"food_identity": "test recipe", "preparation": "cooked",
                         "portion_basis": "100g_edible_portion", "statistic": "sample_measurement"})}
    prop, unit, ctx = specs[kind]
    profile = {"id": "test-only:"+kind, "version": "1", "subject_kind": kind, "properties": {
        prop: {"definition": "TEST ONLY property scope", "type": "number", "unit": unit, "minimum": 0,
               "required_context": list(ctx)}}}
    subject = {"subject_id": "test-subject", "entity_scope": "individual_subject", "subject_kind": kind,
               "context": ctx, "context_evidence": {}, "profile_binding": profile_binding(profile), "assertions": []}
    fact = {"assertion_id": "test-assertion-1", "property_id": prop, "status": "verified", "value": 123,
            "unit": unit, "context": copy.deepcopy(ctx), "producer": "fixture-builder", "data_kind": "sourced_assertion",
            "independent_review": {"state": "accepted", "reference": "fixture://review", "reviewer": "fixture-auditor"},
            "evidence": {"subject_id": "test-subject", "property_id": prop, "context": copy.deepcopy(ctx),
                         "unit": unit, "value": 123, "source_id": "fixture-source", "source_version": "fixture-v1",
                         "locator": "fixture-page", "supporting_text": "TEST ONLY fabricated evidence",
                         "retrieved_at": "2026-11-03T00:00:00Z"}}
    subject["assertions"].append(fact)
    reviewed(fact, subject)
    return profile, subject, fact


class PropertyQueueTests(unittest.TestCase):
    def setUp(self): self.p, self.s, self.f = fixture()
    def queue(self): return inspect_subject(self.s, self.p)["queue"]
    def test_four_profile_fixtures(self):
        for kind in ("deer", "tractor", "weather", "prepared_food"):
            p,s,_ = fixture(kind)
            self.assertEqual(inspect_subject(s,p)["state"], "metadata_requirements_satisfied")
            self.assertEqual(inspect_subject(s,p)["applied"], 0)
    def test_no_raw_mutation(self):
        before=copy.deepcopy(self.s); self.queue(); self.assertEqual(before,self.s)
    def test_absent_property_queued(self):
        self.s["assertions"] = []; self.assertEqual(self.queue()[0]["status"], "absent")
    def test_unresearched_distinct(self):
        self.f["status"] = "unresearched"; self.assertEqual(self.queue()[0]["status"], "unresearched")
    def test_unavailable_not_success(self):
        self.f.update(status="unavailable", reason="Specific search exhausted")
        reviewed(self.f, self.s)
        self.assertEqual(self.queue()[0]["reason"], "evidenced_exception_requires_disposition")
    def test_na_requires_evidence_reason(self):
        self.f["status"]="not_applicable"; self.f.pop("evidence")
        self.assertIn("evidence_binding",self.queue()[0]["reason"])
        self.assertIn("status_reason_required",self.queue()[0]["reason"])
    def test_self_review_rejected(self):
        self.f["independent_review"]["reviewer"]="fixture-builder"
        self.assertIn("independent_review_missing",self.queue()[0]["reason"])
    def test_copy_from_stage_not_verified(self):
        self.f["data_kind"]="inherited_fill_stage"
        self.assertIn("data_kind_not_source_backed",self.queue()[0]["reason"])
    def test_context_mismatch(self):
        self.f["context"]["sex"]="male"
        self.assertIn("context_mismatch:sex",self.queue()[0]["reason"])
    def test_unknown_subject_context(self):
        del self.s["context"]["life_stage"]
        self.assertIn("subject_context_missing:life_stage",self.queue()[0]["reason"])
    def test_wrong_property_evidence(self):
        self.f["evidence"]["property_id"]="standing_height"
        self.assertIn("evidence_binding",self.queue()[0]["reason"])
    def test_units_no_implicit_conversion(self):
        self.f["unit"]="kg"; self.assertIn("unit_mismatch",self.queue()[0]["reason"])
    def test_numeric_boolean_and_nan_rejected(self):
        for value in (True,float("nan"),-1):
            self.f["value"]=value; self.assertTrue(self.queue())
    def test_multiple_values_not_first_wins(self):
        other=copy.deepcopy(self.f);other.update(assertion_id="second",value=124)
        other["evidence"]["value"]=124
        reviewed(other,self.s)
        self.s["assertions"].append(other)
        self.assertEqual(self.queue()[-1]["status"],"conflict")
        self.assertEqual(len(inspect_subject(self.s,self.p)["original"]["assertions"]),2)
    def test_duplicate_assertion_id_blocked(self):
        self.s["assertions"].append(copy.deepcopy(self.f))
        self.assertEqual(inspect_subject(self.s,self.p)["state"],"blocked")
    def test_profile_hash_mismatch(self):
        self.p["version"]="2";self.assertEqual(inspect_subject(self.s,self.p)["state"],"blocked")
    def test_class_scope_not_subject(self):
        self.s["entity_scope"]="class"
        self.assertEqual(inspect_subject(self.s,self.p)["state"],"blocked")
    def test_conditional_unknown_queued(self):
        self.p["properties"]["body_mass"]["when"]={"mass_applicable":True}
        self.s["profile_binding"]=profile_binding(self.p)
        self.assertEqual(self.queue()[0]["reason"],"applicability_unknown")
    def test_condition_reviewed_false(self):
        self.p["properties"]["body_mass"]["when"]={"mass_applicable":True}
        self.s["profile_binding"]=profile_binding(self.p)
        self.s["context"]["mass_applicable"]=False
        self.s["context_evidence"]["mass_applicable"]={"value":False,"source_reference":"fixture://condition",
            "subject_id":"test-subject","context_key":"mass_applicable",
            "producer":"builder","independent_review":{"state":"accepted","reference":"fixture://review","reviewer":"auditor"}}
        reviewed(self.s["context_evidence"]["mass_applicable"],self.s)
        self.s["assertions"]=[]
        self.assertEqual(self.queue(),[])
        self.assertEqual(inspect_subject(self.s,self.p)["assessed"][0]["status"],"not_applicable")
    def test_missing_derivation_not_observed(self):
        self.f["status"]="derived";self.assertIn("explicit_derivation",self.queue()[0]["reason"])
    def test_unreviewed_derivation_input_rejected(self):
        other=copy.deepcopy(self.f);other.update(assertion_id="input",status="unresearched")
        self.s["assertions"].append(other)
        self.f.update(status="derived",derivation={"method":"test expression","input_assertion_ids":["input"]})
        self.assertTrue(any("derivation_inputs_not_reviewed" in q["reason"] for q in self.queue()))
    def test_other_properties_preserved_not_means_fully_covered(self):
        other=copy.deepcopy(self.f);other.update(assertion_id="extra",property_id="color")
        self.s["assertions"].append(other)
        self.assertEqual(inspect_subject(self.s,self.p)["additional_assertions_preserved"],["extra"])
    def test_fingerprint_separates_sources(self):
        a=inspect_subject(self.s,self.p)["assessed"][0]["assertions"][0]["proposed_assertion_fingerprint"]
        self.f["evidence"]["source_version"]="v2"
        b=inspect_subject(self.s,self.p)["assessed"][0]["assertions"][0]["proposed_assertion_fingerprint"]
        self.assertNotEqual(a,b)
    def test_evidence_value_mismatch(self):
        self.f["evidence"]["value"]=999
        self.assertIn("evidence_binding",self.queue()[0]["reason"])
    def test_stale_review_after_value_and_evidence_changed(self):
        self.f["value"] = self.f["evidence"]["value"] = 999999
        self.assertIn("independent_review_missing",self.queue()[0]["reason"])
    def test_stale_review_after_profile_changed(self):
        self.p["version"]="v2";self.s["profile_binding"]=profile_binding(self.p)
        self.assertIn("independent_review_missing",self.queue()[0]["reason"])
    def test_stale_review_after_source_or_context_changed(self):
        for field in ("source", "context"):
            p,s,f=fixture()
            if field=="source": f["evidence"]["source_version"]="changed"
            else:
                s["context"]["sex"]=f["context"]["sex"]=f["evidence"]["context"]["sex"]="male"
            self.assertIn("independent_review_missing",inspect_subject(s,p)["queue"][0]["reason"])
    def test_condition_proof_cannot_move_between_subjects_or_profiles(self):
        self.test_condition_reviewed_false()
        baseline=copy.deepcopy(self.s)
        for change in ("subject", "profile", "value"):
            s=copy.deepcopy(baseline); p=copy.deepcopy(self.p)
            if change=="subject": s["subject_id"]="different-subject"
            elif change=="profile":
                p["version"]="different";s["profile_binding"]=profile_binding(p)
            else: s["context"]["mass_applicable"]=True
            self.assertEqual(inspect_subject(s,p)["queue"][0]["reason"],"applicability_unknown")
    def test_derived_cannot_be_observed(self):
        self.f["data_kind"]="derived_assertion";reviewed(self.f,self.s)
        self.assertIn("derived_or_inherited_not_observed",self.queue()[0]["reason"])
    def test_inapplicability_does_not_hide_conflict(self):
        self.p["properties"]["body_mass"]["when"]={"mass_applicable":True}
        self.s["profile_binding"]=profile_binding(self.p);self.s["context"]["mass_applicable"]=False
        proof={"value":False,"source_reference":"fixture://condition","subject_id":"test-subject","context_key":"mass_applicable",
            "producer":"builder","independent_review":{"state":"accepted","reference":"fixture://review","reviewer":"auditor"}}
        reviewed(proof,self.s);self.s["context_evidence"]["mass_applicable"]=proof
        self.f["status"]="conflict"
        self.assertEqual(self.queue()[0]["status"],"conflict")
        self.assertEqual(inspect_subject(self.s,self.p)["assessed"][0]["assertions"][0]["status"],"conflict")
    def test_conflicted_observation_cannot_support_derivation(self):
        self.p["properties"]["derived_mass"] = copy.deepcopy(self.p["properties"]["body_mass"])
        self.s["profile_binding"]=profile_binding(self.p);reviewed(self.f,self.s)
        second=copy.deepcopy(self.f);second.update(assertion_id="second",value=124);second["evidence"]["value"]=124;reviewed(second,self.s)
        derived=copy.deepcopy(self.f);derived.update(assertion_id="derived",property_id="derived_mass",status="derived",data_kind="derived_assertion",
            derivation={"method":"test expression","input_assertion_ids":[self.f["assertion_id"]]})
        derived["evidence"]["property_id"]="derived_mass";reviewed(derived,self.s)
        self.s["assertions"] += [second,derived]
        self.assertTrue(any(q["reason"]=="derivation_inputs_not_reviewed_observations" for q in self.queue()))
    def test_split_tractor_paths_preserved_candidates(self):
        # Shape from legacy tractor document; numeric values are synthetic tests.
        raw={"dimensional_specifications_mm":{"length_mm":111},"mass_specifications_g":{"operating_mass_g":222},"citation":None}
        result=extract_candidates(raw,"fixture-source",{"length":[["dimensional_specifications_mm","length_mm"]],
            "operating_mass":[["mass_specifications_g","operating_mass_g"]]})
        self.assertEqual(len(result["candidates"]),2)
        self.assertTrue(all(x["status"]=="unresearched" for x in result["candidates"]))
        self.assertEqual(raw,result["original"])
    def test_deer_range_not_scalar_or_wingspan_height(self):
        raw={"morphometric_specifications_mm_g":{"mass_and_physiological_range":{"min_max_mass_range_g":[111,222]},
            "overall_bounding_box_mm":{"wingspan_or_canopy_spread_mm":333}}}
        result=extract_candidates(raw,"fixture-source",{"body_mass_range":[["morphometric_specifications_mm_g","mass_and_physiological_range","min_max_mass_range_g"]],
            "standing_height":[["morphometric_specifications_mm_g","overall_bounding_box_mm","standing_height_mm"]]})
        self.assertEqual(len(result["candidates"]),1)
        self.assertEqual(result["candidates"][0]["value"],[111,222])

if __name__ == "__main__": unittest.main()
