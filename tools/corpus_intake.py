"""Staging adapter for legacy CSV and reviewed assertion envelopes. No loader."""
import csv
import hashlib
import json
import io
from pathlib import Path
from .taxonomy_guard import inspect_record, strict_json, validate_registry
from .property_gap_queue import inspect_subject, profile_binding


def assess_row(raw, registry=None, profiles=None):
    """Preserve raw records; no classifications or facts are inferred/defaulted.

    Legacy CSV may carry taxonomy_record_json and property_subject_json columns.
    They must explicitly bind to existing legacy identity/classification fields.
    """
    result = {"state": "needs_research", "original": raw, "reasons": [], "applied": 0}
    if registry is None or not profiles:
        result["reasons"].append("explicit_registry_and_profiles_required")
        return result
    try:
        validate_registry(registry)
        if registry.get("authority_state") != "approved":
            raise ValueError("registry_authority_unresolved")
        for p in profiles.values(): profile_binding(p)
        record = raw.get("taxonomy_record")
        if record is None and raw.get("taxonomy_record_json"):
            record = strict_json(raw["taxonomy_record_json"])
        subject = raw.get("property_subject")
        if subject is None and raw.get("property_subject_json"):
            subject = strict_json(raw["property_subject_json"])
        if not isinstance(record, dict) or not isinstance(subject, dict):
            raise ValueError("explicit_taxonomy_record_and_property_subject_required")
        legacy_key = raw.get("canonical_dedup_key") or raw.get("dedup_key")
        if not legacy_key or legacy_key != record.get("canonical_dedup_key"):
            raise ValueError("legacy_key_disagreement_or_missing")
        # Binding the stable subject is explicit; no category/region-expanded ID inference.
        if not raw.get("subject_id") or raw["subject_id"] != subject.get("subject_id"):
            raise ValueError("stable_subject_binding_missing_or_wrong")
        if record.get("subject_id") != subject["subject_id"]:
            raise ValueError("taxonomy_subject_disagreement")
        for key in ("category_code", "region_code", "era_code", "master_variant"):
            if key in raw and raw[key] != record.get(key):
                raise ValueError("legacy_" + key + "_disagreement")
        profile_id = subject.get("profile_binding", {}).get("id")
        if profile_id not in profiles: raise ValueError("unknown_property_profile")
        taxonomy = inspect_record(record, registry)
        for axis, table in (("category","categories"),("region","regions"),("era","eras")):
            code=record.get("classifications",{}).get(axis,{}).get("code")
            if registry[table].get(code,{}).get("status") != "approved":
                raise ValueError("classification_entry_unresolved:"+axis)
        properties = inspect_subject(subject, profiles[profile_id])
        result.update(taxonomy=taxonomy, properties=properties)
        if taxonomy["state"] != "eligible_for_independent_review":
            result["reasons"].extend(taxonomy["reasons"])
        if properties["state"] != "metadata_requirements_satisfied":
            result["reasons"].append("property_review_required")
        if not result["reasons"]:
            # Neither module authenticates sources/reviewers: stage only, never verified/applied.
            result["state"] = "eligible_for_independent_review"
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        result["reasons"].append(str(exc))
    return result


def compile_csv(csv_path, out_path, registry=None, profiles=None, content_addressed=False):
    source = Path(csv_path)
    if source.resolve() == Path(out_path).resolve():
        raise ValueError("report_must_not_replace_source")
    content = source.read_bytes()
    source_hash = hashlib.sha256(content).hexdigest()
    results, seen = [], set()
    with io.StringIO(content.decode("utf-8"), newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("missing_or_duplicate_csv_headers")
        for line, raw in enumerate(reader, 2):
            result = assess_row(raw, registry, profiles)
            if None in raw or any(v is None for v in raw.values()):
                result["state"]="needs_research"
                result["reasons"].append("ragged_csv_row")
            key = raw.get("canonical_dedup_key") or raw.get("dedup_key")
            if key and key in seen:
                result["state"] = "needs_research"
                result["reasons"].append("duplicate_legacy_key_in_input")
                for previous in results:
                    old=previous["original"]
                    if (old.get("canonical_dedup_key") or old.get("dedup_key")) == key:
                        previous["state"]="needs_research"
                        if "duplicate_legacy_key_in_input" not in previous["reasons"]:
                            previous["reasons"].append("duplicate_legacy_key_in_input")
            if key: seen.add(key)
            result.update(source_path=str(source), source_sha256=source_hash, source_line=line)
            results.append(result)
    # Deliberately a review-report envelope, never a loader-ready blocks record.
    target = Path(out_path)
    if content_addressed:
        identity = json.dumps({"source_path":str(source.resolve()),"source_sha256":source_hash,
                               "registry":registry,"profiles":profiles},sort_keys=True,allow_nan=False)
        run_hash=hashlib.sha256(identity.encode()).hexdigest()
        target=target.with_name(target.stem+"-"+run_hash+".jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload="".join(json.dumps(r, ensure_ascii=False, allow_nan=False)+"\n" for r in results)
    reused=False
    try:
        with target.open("x",encoding="utf-8") as out:out.write(payload)
    except FileExistsError:
        if target.read_text(encoding="utf-8") != payload:
            raise ValueError("existing_report_differs_refuse_overwrite")
        reused=True
    eligible = sum(r["state"] == "eligible_for_independent_review" for r in results)
    return {"input_rows": len(results), "staged_reports": len(results), "eligible_for_independent_review": eligible,
            "needs_research": len(results)-eligible, "applied": 0, "source_validated": 0,
            "source_sha256": source_hash, "report_path": str(target), "reused_report": reused}


def load_contract(registry_path=None, profiles_path=None):
    if not registry_path or not profiles_path: return None, None
    registry = strict_json(Path(registry_path).read_text(encoding="utf-8"))
    profiles = strict_json(Path(profiles_path).read_text(encoding="utf-8"))
    validate_registry(registry)
    if not isinstance(profiles, dict) or not profiles: raise ValueError("profiles map required")
    for key, profile in profiles.items():
        if profile_binding(profile)["id"] != key: raise ValueError("profile map key disagreement")
    return registry, profiles
