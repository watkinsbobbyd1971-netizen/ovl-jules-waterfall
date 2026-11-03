import json
import sys

def main():
    lines = open(sys.argv[1]).read().splitlines()
    print(len(lines))
    for l in lines:
        if l.strip():
            d = json.loads(l)
            print(f"{d['canonical_dedup_key']} | {d['verification_citation_url']}")

if __name__ == '__main__':
    main()
