import contextlib
import copy
import csv
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_taxonomy_guard import fixture as tax_fixture
from test_property_gap_queue import fixture as fact_fixture
from tools.taxonomy_guard import validate_registry
from tools.corpus_intake import assess_row, compile_csv
import jules_waterfall_worker as worker
import antigravity_autonomous_daemon as daemon


def envelope():
    registry,record=tax_fixture();profile,subject,_=fact_fixture()
    registry["authority_state"]="approved"
    for table in ("categories","regions","eras"):
        for entry in registry[table].values():entry["status"]="approved"
    record["taxonomy_binding"]=validate_registry(registry)
    record["subject_id"]=subject["subject_id"]
    raw={"dedup_key":record["canonical_dedup_key"],"subject_id":subject["subject_id"],
         "taxonomy_record_json":json.dumps(record),"property_subject_json":json.dumps(subject)}
    return registry,{profile["id"]:profile},raw


class IntakeTests(unittest.TestCase):
    def setUp(self):self.reg,self.profiles,self.raw=envelope()
    def write(self,path,rows):
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("w",newline="") as f:
            out=csv.DictWriter(f,fieldnames=list(rows[0]));out.writeheader();out.writerows(rows)
    def test_bound_envelope_is_review_only(self):
        before=copy.deepcopy(self.raw);r=assess_row(self.raw,self.reg,self.profiles)
        self.assertEqual(r["state"],"eligible_for_independent_review")
        self.assertEqual(r["applied"],0);self.assertEqual(self.raw,before)
    def test_legacy_without_bindings_never_defaults(self):
        raw={"dedup_key":"old","verified_facts":"bad-json"}
        r=assess_row(raw,self.reg,self.profiles)
        self.assertEqual(r["state"],"needs_research");self.assertEqual(r["original"],raw)
        self.assertNotIn("region_code",r)
    def test_registry_proposal_held(self):
        self.reg["authority_state"]="proposed"
        self.assertIn("registry_authority_unresolved",assess_row(self.raw,self.reg,self.profiles)["reasons"])
    def test_legacy_disagreement(self):
        self.raw["region_code"]="WRONG"
        self.assertIn("legacy_region_code_disagreement",assess_row(self.raw,self.reg,self.profiles)["reasons"])
    def test_taxonomy_cannot_be_other_subject(self):
        record=json.loads(self.raw["taxonomy_record_json"]);record["subject_id"]="other"
        self.raw["taxonomy_record_json"]=json.dumps(record)
        self.assertIn("taxonomy_subject_disagreement",assess_row(self.raw,self.reg,self.profiles)["reasons"])
    def test_duplicate_holds_both(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"a.csv";out=Path(d)/"a.jsonl";self.write(src,[self.raw,self.raw])
            r=compile_csv(src,out,self.reg,self.profiles)
            self.assertEqual(r["eligible_for_independent_review"],0)
            self.assertEqual(r["needs_research"],2)
    def test_same_basename_distinct_report(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/part/"batch_01.csv" for part in ("a","b")]
            for p in paths:self.write(p,[self.raw])
            reports=[daemon.process_batch_file(p,self.reg,self.profiles,Path(d)/"out") for p in paths]
            self.assertNotEqual(reports[0]["report_path"],reports[1]["report_path"])
    def test_source_or_contract_changes_keep_prior_report(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"batch.csv";self.write(src,[self.raw])
            first=daemon.process_batch_file(src,self.reg,self.profiles,Path(d)/"out")
            original=Path(first["report_path"]).read_bytes()
            changed=copy.deepcopy(self.raw);changed["note"]="new raw version";self.write(src,[changed])
            second=daemon.process_batch_file(src,self.reg,self.profiles,Path(d)/"out")
            self.reg["source_reference"]="fixture://new-contract"
            third=daemon.process_batch_file(src,self.reg,self.profiles,Path(d)/"out")
            self.assertEqual(len({r["report_path"] for r in (first,second,third)}),3)
            self.assertEqual(Path(first["report_path"]).read_bytes(),original)
    def test_source_path_cannot_be_output(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"a.csv";self.write(src,[self.raw]);before=src.read_bytes()
            with self.assertRaisesRegex(ValueError,"must_not_replace_source"):
                compile_csv(src,src,self.reg,self.profiles)
            self.assertEqual(src.read_bytes(),before)
    def test_ragged_csv_held(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"a.csv";src.write_text("dedup_key,subject_id\nlegacy\n")
            result=compile_csv(src,Path(d)/"out.jsonl",self.reg,self.profiles)
            self.assertEqual(result["needs_research"],1)
            self.assertIn("ragged_csv_row",json.loads(Path(result["report_path"]).read_text())["reasons"])
    def test_failed_application_never_invokes_bq(self):
        with patch("subprocess.run") as run,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(daemon.main(["--profile","1","--apply"]),2)
            run.assert_not_called()
    def test_shared_batch_not_profile_evidence(self):
        with tempfile.TemporaryDirectory() as d,patch("os.getcwd",return_value=d):
            with patch("os.path.isfile",side_effect=lambda p:p=="queue_batch_01.csv"):
                self.assertIsNone(worker.find_batch_csv(1,1))
    def test_loop_bounded_and_skips_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            old=os.getcwd();os.chdir(d)
            try:
                self.write(Path("batches/profile-1/batch_01.csv"),[self.raw])
                output=io.StringIO();sleeps=[]
                with contextlib.redirect_stdout(output):code=daemon.main(["--profile","1","--loop","--max-rounds","2","--poll-seconds","0"],sleep=sleeps.append)
                rows=[json.loads(x) for x in output.getvalue().splitlines()]
                self.assertEqual(code,1);self.assertEqual(len(rows),2)
                self.assertEqual(rows[1]["reports"],[]);self.assertEqual(sleeps,[0])
                self.assertEqual(rows[0]["applied"],0)
            finally:os.chdir(old)
    def test_real_worker_entrypoint_holds_old_source(self):
        with tempfile.TemporaryDirectory() as d:
            old=os.getcwd();os.chdir(d)
            try:
                self.write(Path("batches/profile-1/batch_01.csv"),[{"dedup_key":"legacy","verified_facts":"{}"}])
                with patch.dict(os.environ,{"OVL_PROFILE":"1"}),contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(worker.main(["1"]),1)
                self.assertEqual(len(list(Path("review-output/profile-1").glob("*.jsonl"))),1)
                self.assertFalse(Path("output").exists())
            finally:os.chdir(old)


if __name__=="__main__":unittest.main()
