#!/usr/bin/env python3
"""Compile source rows into isolated review reports, never fabricated corpus facts."""
import argparse
import glob
import json
import os
import re
import subprocess
from tools.corpus_intake import compile_csv, load_contract


def compile_csv_to_jsonl(csv_path, out_path, registry=None, profiles=None):
    return compile_csv(csv_path, out_path, registry, profiles)


def detect_profile():
    override = os.environ.get("OVL_PROFILE", "").strip()
    if override:
        match = re.fullmatch(r"(?:profile-)?([1-6])", override)
        if not match: raise ValueError("OVL_PROFILE must identify profile 1..6")
        return int(match[1])
    refs = [os.environ.get("GITHUB_HEAD_REF"), os.environ.get("GITHUB_REF_NAME")]
    try:
        refs.append(subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True,
                                           stderr=subprocess.DEVNULL).strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    for ref in refs:
        match = re.match(r"profile-([1-6])(?:-|$)", ref or "")
        if match: return int(match[1])
    return None


def find_batch_csv(profile, batch):
    # Shared batches have no account/profile ownership proof. Explicitly reject fallback.
    path = f"batches/profile-{profile}/batch_{batch:02d}.csv"
    return path if os.path.isfile(path) else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batches", nargs="*", type=int)
    parser.add_argument("--registry")
    parser.add_argument("--profiles")
    args = parser.parse_args(argv)
    try:
        profile = detect_profile()
        if profile is None:
            print(json.dumps({"state":"blocked", "reason":"explicit_profile_required", "applied":0})); return 2
        registry, profiles = load_contract(args.registry, args.profiles)
        if len(args.batches)>2 or any(b<1 for b in args.batches): raise ValueError("one batch or bounded increasing range required")
        if len(args.batches)==2:
            if args.batches[1]<args.batches[0] or args.batches[1]-args.batches[0]>1000: raise ValueError("invalid batch range")
            batches=range(args.batches[0],args.batches[1]+1)
        elif args.batches: batches=args.batches
        else:
            batches=sorted(int(re.search(r"batch_(\d+)\.csv$",p)[1]) for p in glob.glob(f"batches/profile-{profile}/batch_*.csv") if re.search(r"batch_(\d+)\.csv$",p))
        reports=[]; missing=[]
        for batch in batches:
            path=find_batch_csv(profile,batch)
            if path is None: missing.append(batch); continue
            reports.append(compile_csv(path,f"review-output/profile-{profile}/batch_{batch:02d}.review.jsonl",registry,profiles,content_addressed=True))
        print(json.dumps({"state":"review_reports_written" if reports else "blocked", "reports":reports,
                          "missing_batches":missing,"applied":0,"source_validated":0}))
        return 1 if missing or not reports or any(r["needs_research"] for r in reports) else 0
    except (ValueError,OSError) as exc:
        print(json.dumps({"state":"blocked","reason":str(exc),"applied":0})); return 2


if __name__=="__main__": raise SystemExit(main())
