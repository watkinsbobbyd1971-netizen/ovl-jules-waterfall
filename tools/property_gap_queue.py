"""Offline requirement-profile inspector; no network, database, or file writes."""
import hashlib
import json
import math

STATUSES = {"absent", "unresearched", "unavailable", "not_applicable", "conflict", "verified", "derived"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def text(value):
    return isinstance(value, str) and bool(value.strip())


def fingerprint(value):
    try:
        return digest(value)
    except (ValueError, TypeError):
        return None


def profile_binding(profile):
    if not isinstance(profile, dict) or not all(text(profile.get(k)) for k in ("id", "version", "subject_kind")):
        raise ValueError("profile identity/version/subject kind required")
    properties = profile.get("properties")
    if not isinstance(properties, dict) or not properties:
        raise ValueError("explicit properties required")
    for name, spec in properties.items():
        if not text(name) or not isinstance(spec, dict) or spec.get("type") not in ("number", "string"):
            raise ValueError("invalid property type")
        if not text(spec.get("definition")) or not isinstance(spec.get("required_context"), list):
            raise ValueError("property definition and context policy required")
        if not all(text(k) for k in spec["required_context"]):
            raise ValueError("invalid context key")
        if spec["type"] == "number" and not text(spec.get("unit")):
            raise ValueError("numeric unit required")
        if "when" in spec and (not isinstance(spec["when"], dict) or not spec["when"]):
            raise ValueError("invalid condition")
    return {"id": profile["id"], "version": profile["version"], "sha256": digest(profile)}


def review_digest(item, subject_id, binding):
    return fingerprint({"subject_id": subject_id, "profile_binding": binding,
                        "assertion": {k: v for k, v in item.items() if k != "independent_review"}})


def has_review(item, subject_id, binding):
    review = item.get("independent_review")
    return (isinstance(review, dict) and review.get("state") == "accepted"
            and text(review.get("reference")) and text(review.get("reviewer"))
            and text(item.get("producer")) and review["reviewer"] != item["producer"]
            and text(review.get("reviewed_digest"))
            and review["reviewed_digest"] == review_digest(item, subject_id, binding))


def evidence_ok(item, subject_id, property_id):
    evidence = item.get("evidence")
    if not isinstance(evidence, dict):
        return False
    return (all(text(evidence.get(k)) for k in ("source_id", "source_version", "locator", "supporting_text", "retrieved_at"))
            and evidence.get("subject_id") == subject_id
            and evidence.get("property_id") == property_id
            and evidence.get("context") == item.get("context")
            and (item.get("status") not in ("verified", "derived") or evidence.get("value") == item.get("value")))


def applicability(spec, subject, binding):
    """Conditions use independently reviewed subject context, never guessed kind."""
    conditions = spec.get("when", {})
    context = subject.get("context", {})
    proofs = subject.get("context_evidence", {})
    for key in conditions:
        proof = proofs.get(key)
        if key not in context or not isinstance(proof, dict) or not has_review(proof, subject.get("subject_id"), binding):
            return "unknown"
        if (not text(proof.get("source_reference")) or proof.get("value") != context[key]
                or proof.get("subject_id") != subject.get("subject_id") or proof.get("context_key") != key):
            return "unknown"
    return "applicable" if all(context[k] == v for k, v in conditions.items()) else "not_applicable"


def inspect_subject(subject, profile):
    """Returns a queue plus assessed assertions; never promotes or modifies facts."""
    binding = profile_binding(profile)
    if not isinstance(subject, dict):
        raise ValueError("subject must be an object")
    sid = subject.get("subject_id")
    if not text(sid) or subject.get("entity_scope") != "individual_subject":
        return {"state": "blocked", "reasons": ["exact_subject_identity_required"], "original": subject}
    if subject.get("profile_binding") != binding or subject.get("subject_kind") != profile["subject_kind"]:
        return {"state": "blocked", "reasons": ["profile_binding_or_kind_mismatch"], "original": subject}
    facts = subject.get("assertions", [])
    context = subject.get("context", {})
    if not isinstance(facts, list) or not isinstance(context, dict) or not isinstance(subject.get("context_evidence", {}), dict):
        raise ValueError("invalid assertions/context")
    if any(not isinstance(f, dict) or not text(f.get("property_id")) or not text(f.get("assertion_id")) for f in facts):
        raise ValueError("assertions require distinct identity and property")
    ids = [f["assertion_id"] for f in facts]
    if len(ids) != len(set(ids)):
        return {"state": "blocked", "reasons": ["duplicate_assertion_id"], "original": subject}
    queue, assessed, eligible_ids, derived_checks = [], [], set(), []
    for prop, spec in profile["properties"].items():
        app = applicability(spec, subject, binding)
        candidates = [f for f in facts if f["property_id"] == prop]
        result = {"property_id": prop, "applicability": app, "assertions": []}
        if app == "unknown":
            queue.append({"property_id": prop, "status": "absent", "reason": "applicability_unknown"})
            assessed.append(result)
            continue
        if app == "not_applicable":
            result["status"] = "not_applicable"
            result["basis"] = "reviewed_profile_condition"
            if candidates:
                queue.append({"property_id": prop, "status": "conflict", "reason": "assertions_present_for_inapplicable_property"})
                result["assertions"] = [{"assertion_id": f["assertion_id"], "status": f.get("status"),
                    "reasons": ["assertion_conflicts_with_reviewed_inapplicability"]} for f in candidates]
            assessed.append(result)
            continue
        if not candidates:
            queue.append({"property_id": prop, "status": "absent", "reason": "no_assertion"})
        valid_values = []
        for fact in candidates:
            reasons = []
            status = fact.get("status")
            fcontext = fact.get("context")
            if status not in STATUSES:
                reasons.append("unknown_status")
            if not isinstance(fcontext, dict):
                reasons.append("context_not_object")
                fcontext = {}
            for key in spec["required_context"]:
                if key not in context or context[key] is None or context[key] == "":
                    reasons.append("subject_context_missing:" + key)
                elif fcontext.get(key) != context[key]:
                    reasons.append("context_mismatch:" + key)
            if status in ("verified", "derived", "unavailable", "not_applicable"):
                if fact.get("data_kind") not in ("sourced_assertion", "derived_assertion"):
                    reasons.append("data_kind_not_source_backed")
                if status == "verified" and fact.get("data_kind") != "sourced_assertion":
                    reasons.append("derived_or_inherited_not_observed")
                if status == "derived" and fact.get("data_kind") != "derived_assertion":
                    reasons.append("derived_kind_required")
                if not evidence_ok(fact, sid, prop):
                    reasons.append("evidence_binding_missing_or_wrong")
                if not has_review(fact, sid, binding):
                    reasons.append("independent_review_missing")
            if status in ("verified", "derived"):
                value = fact.get("value")
                if spec["type"] == "number":
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                        reasons.append("invalid_numeric_value")
                    else:
                        if "minimum" in spec and value < spec["minimum"]:
                            reasons.append("below_profile_minimum")
                        if "maximum" in spec and value > spec["maximum"]:
                            reasons.append("above_profile_maximum")
                    if fact.get("unit") != spec["unit"]:
                        reasons.append("unit_mismatch_no_implicit_conversion")
                    if isinstance(fact.get("evidence"), dict) and fact["evidence"].get("unit") != fact.get("unit"):
                        reasons.append("evidence_unit_mismatch")
                elif not text(value):
                    reasons.append("invalid_text_value")
                if status == "derived":
                    derivation = fact.get("derivation")
                    if not isinstance(derivation, dict) or not text(derivation.get("method")) or not derivation.get("input_assertion_ids"):
                        reasons.append("explicit_derivation_required")
                    elif not all(i in ids and i != fact["assertion_id"] for i in derivation["input_assertion_ids"]):
                        reasons.append("derivation_inputs_missing")
                    else:
                        derived_checks.append((prop, fact))
                if not reasons:
                    valid_values.append((digest({"value": value, "unit": fact.get("unit"), "context": fcontext}), fact["assertion_id"]))
                    if status == "verified":
                        eligible_ids.add(fact["assertion_id"])
            elif status in ("unavailable", "not_applicable"):
                if not text(fact.get("reason")):
                    reasons.append("status_reason_required")
            else:
                reasons.append("research_or_conflict_resolution_needed")
            assessment = {"assertion_id": fact["assertion_id"], "status": status, "reasons": reasons,
                          "proposed_assertion_fingerprint": fingerprint({"subject_id": sid, "property_id": prop,
                              "context": fact.get("context"), "source": fact.get("evidence"),
                              "value": fact.get("value"), "unit": fact.get("unit"), "status": status})}
            result["assertions"].append(assessment)
            if reasons or status in ("unavailable", "not_applicable"):
                queue.append({"property_id": prop, "assertion_id": fact["assertion_id"], "status": status,
                              "reason": ";".join(reasons) or "evidenced_exception_requires_disposition"})
        if len({x[0] for x in valid_values}) > 1:
            queue.append({"property_id": prop, "status": "conflict", "reason": "multiple_values_same_required_property",
                          "assertion_ids": [x[1] for x in valid_values]})
            eligible_ids.difference_update(x[1] for x in valid_values)
        assessed.append(result)
    # v1 only accepts direct independently-reviewed observed inputs; no chained
    # derivation or cycle is silently treated as a validated input.
    for prop, fact in derived_checks:
        if any(i not in eligible_ids for i in fact["derivation"]["input_assertion_ids"]):
            queue.append({"property_id": prop, "assertion_id": fact["assertion_id"], "status": "derived",
                          "reason": "derivation_inputs_not_reviewed_observations"})
            for item in assessed:
                for assertion in item["assertions"]:
                    if assertion["assertion_id"] == fact["assertion_id"]:
                        assertion["reasons"].append("derivation_inputs_not_reviewed_observations")
    unknown = [f["assertion_id"] for f in facts if f["property_id"] not in profile["properties"]]
    return {"state": "review_required" if queue else "metadata_requirements_satisfied",
            "subject_id": sid, "profile_binding": binding, "queue": queue, "assessed": assessed,
            "additional_assertions_preserved": unknown, "original": subject, "applied": 0}


def extract_candidates(raw_block, source_id, property_paths):
    """Explicit adapter paths only. Keeps values as unreviewed candidates, never facts.

    property_paths maps semantic property IDs to lists of field-token paths.
    No aliases such as wingspan=>height, no unit/statistic conversions or defaults.
    """
    if not isinstance(raw_block, dict) or not text(source_id):
        raise ValueError("source object and source identity required")
    candidates = []
    for prop, paths in property_paths.items():
        for path in paths:
            value = raw_block
            for key in path:
                if not isinstance(value, dict) or key not in value:
                    break
                value = value[key]
            else:
                candidates.append({"candidate_id": fingerprint({"source_id": source_id, "path": path, "value": value}),
                    "property_id": prop, "value": value, "source_id": source_id, "source_path": list(path),
                    "data_kind": "inherited_original_block", "status": "unresearched",
                    "unit": None, "context": {}, "independent_review": None})
    return {"candidates": candidates, "original": raw_block, "source_id": source_id, "applied": 0}
