#!/usr/bin/env python3
"""Bounded offline review staging. Production application belongs to the designated writer."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from tools.corpus_intake import compile_csv, load_contract


def process_batch_file(csv_path, registry=None, profiles=None, output_root="review-output/antigravity"):
    source=Path(csv_path)
    target=Path(output_root)/f"{source.stem}.review.jsonl"
    return compile_csv(source,target,registry,profiles,content_addressed=True)


def main(argv=None, sleep=time.sleep):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile",required=True,choices=[str(i) for i in range(1,7)])
    parser.add_argument("--registry"); parser.add_argument("--profiles")
    parser.add_argument("--workers",type=int,default=1,help="Compatibility option; this bounded staging path is sequential")
    mode=parser.add_mutually_exclusive_group();mode.add_argument("--once",action="store_true");mode.add_argument("--loop",action="store_true")
    parser.add_argument("--max-rounds",type=int,default=1);parser.add_argument("--poll-seconds",type=float,default=5)
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args(argv)
    if args.apply:
        print(json.dumps({"state":"blocked","reason":"designated_validated_writer_required","applied":0}));return 2
    try:
        if args.max_rounds<1 or args.max_rounds>1000 or args.poll_seconds<0:raise ValueError("bounded rounds/poll required")
        registry,profiles=load_contract(args.registry,args.profiles)
        errors=False; found=False
        for round_number in range(args.max_rounds if args.loop else 1):
            reports=[]
            for source in sorted(Path(f"batches/profile-{args.profile}").glob("batch_*.csv")):
                found=True
                report=process_batch_file(source,registry,profiles)
                errors |= bool(report["needs_research"])
                if not report["reused_report"]:reports.append(report)
            print(json.dumps({"round":round_number+1,"reports":reports,"applied":0,"source_validated":0}))
            if args.loop and round_number+1<args.max_rounds:sleep(args.poll_seconds)
        return 1 if errors or not found else 0
    except KeyboardInterrupt:
        print(json.dumps({"state":"interrupted","applied":0}));return 130
    except (ValueError,OSError) as exc:
        print(json.dumps({"state":"blocked","reason":str(exc),"applied":0}));return 2


if __name__=="__main__":raise SystemExit(main())
