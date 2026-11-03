#!/usr/bin/env python3
"""Offline taxonomy discrepancy reporter. Never rewrites records or loads data."""
import argparse
import hashlib
import json
import sys

AXES = {"category": "categories", "region": "regions", "era": "eras"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_registry(registry):
    if not isinstance(registry, dict):
        raise ValueError("registry must be an object")
    if not all(nonempty(registry.get(k)) for k in ("registry_id", "taxonomy_version", "source_reference")):
        raise ValueError("explicit registry identity, taxonomy version and source reference required")
    for axis, table in AXES.items():
        entries = registry.get(table)
        if not isinstance(entries, dict) or not entries:
            raise ValueError("missing explicit " + table)
        meanings = set()
        for code, entry in entries.items():
            if not nonempty(code) or not isinstance(entry, dict) or not all(
                    nonempty(entry.get(k)) for k in ("semantic_id", "label", "definition")):
                raise ValueError("incomplete registry definition: " + str(code))
            if entry["semantic_id"] in meanings:
                raise ValueError("duplicate semantic identity in " + table)
            meanings.add(entry["semantic_id"])
            if axis == "category" and (not isinstance(entry.get("allowed_variants"), list)
                    or not entry["allowed_variants"]
                    or not all(nonempty(v) for v in entry["allowed_variants"])):
                raise ValueError("explicit category variant policy required")
    return {"registry_id": registry["registry_id"],
            "taxonomy_version": registry["taxonomy_version"], "registry_sha256": digest(registry)}


def inspect_record(record, registry):
    """Eligible means classification metadata is reviewable, never factual acceptance."""
    binding = validate_registry(registry)
    reasons = []
    if not isinstance(record, dict):
        return {"state": "unresolved", "reasons": ["record_not_object"], "original": record}
    if record.get("taxonomy_binding") != binding:
        reasons.append("missing_or_mismatched_taxonomy_binding")
    key = record.get("canonical_dedup_key")
    if not nonempty(key):
        reasons.append("missing_canonical_key")
    classifications = record.get("classifications")
    if not isinstance(classifications, dict):
        classifications = {}
    for axis, table in AXES.items():
        value = classifications.get(axis)
        if not isinstance(value, dict):
            reasons.append(axis + ":missing_classification")
            continue
        code = value.get("code")
        definition = registry[table].get(code) if isinstance(code, str) else None
        if definition is None:
            reasons.append(axis + ":unknown_code")
            continue
        if value.get("semantic_id") != definition["semantic_id"] or value.get("label") != definition["label"]:
            reasons.append(axis + ":code_meaning_disagreement")
        # Never silently prefer the proposed tuple over a legacy top-level code.
        if record.get(axis + "_code", code) != code:
            reasons.append(axis + ":legacy_code_disagreement")
        for location, legacy in (("top_level", record),
                                 ("temporal_anchor", record.get("temporal_and_dedup_anchor"))):
            if legacy is None:
                continue
            if not isinstance(legacy, dict):
                reasons.append(location + ":invalid_object")
                continue
            for field, expected in ((axis + "_code", code), (axis + "_name", definition["label"])):
                if field in legacy and legacy[field] != expected:
                    reasons.append(axis + ":" + location + "_" + field + "_disagreement")
        evidence = value.get("evidence")
        if not isinstance(evidence, dict):
            reasons.append(axis + ":missing_evidence")
        else:
            if evidence.get("kind") not in ("observed", "explicitly_derived"):
                reasons.append(axis + ":unsupported_evidence_kind")
            if not all(nonempty(evidence.get(k)) for k in
                       ("source_reference", "source_record_id", "supporting_evidence", "retrieved_utc")):
                reasons.append(axis + ":incomplete_evidence")
            if evidence.get("kind") == "explicitly_derived" and not nonempty(evidence.get("derivation")):
                reasons.append(axis + ":missing_derivation")
        if axis == "category" and record.get("master_variant") not in definition["allowed_variants"]:
            reasons.append("category:variant_disagreement")
    return {"state": "unresolved" if reasons else "eligible_for_independent_review",
            "canonical_dedup_key": key, "reasons": reasons, "original": record}


def compare_registries(left, right):
    """Report meaning drift; do not choose either registry as authoritative."""
    a, b = validate_registry(left), validate_registry(right)
    changes = []
    for axis, table in AXES.items():
        for code in sorted(set(left[table]) | set(right[table])):
            if left[table].get(code) != right[table].get(code):
                changes.append({"axis": axis, "code": code,
                                "left": left[table].get(code), "right": right[table].get(code)})
    return {"left_binding": a, "right_binding": b, "differences": changes,
            "same_version_different_content": a["taxonomy_version"] == b["taxonomy_version"]
            and a["registry_sha256"] != b["registry_sha256"]}


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON number")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--records", required=True, help="JSONL input; output report goes to stdout")
    args = ap.parse_args(argv)
    try:
        with open(args.registry, encoding="utf-8") as stream:
            registry = strict_json(stream.read())
        validate_registry(registry)
    except (ValueError, OSError) as exc:
        print(json.dumps({"state": "blocked", "reason": str(exc)}))
        return 2
    unresolved, count, seen = 0, 0, set()
    try:
        with open(args.records, encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                count += 1
                try:
                    result = inspect_record(strict_json(line), registry)
                    key = result.get("canonical_dedup_key")
                    if isinstance(key, str) and key in seen:
                        result["state"] = "unresolved"
                        result["reasons"].append("duplicate_canonical_key")
                    if isinstance(key, str):
                        seen.add(key)
                except ValueError as exc:
                    result = {"state": "unresolved", "reasons": ["invalid_json: " + str(exc)],
                              "original_text": line.rstrip("\n")}
                result["line"] = line_number
                unresolved += result["state"] == "unresolved"
                print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except OSError as exc:
        print(json.dumps({"state": "blocked", "reason": str(exc)}))
        return 2
    print(json.dumps({"summary": {"records": count, "unresolved": unresolved,
          "eligible_for_independent_review": count - unresolved, "applied": 0}}))
    return 1 if unresolved or not count else 0


if __name__ == "__main__":
    sys.exit(main())
