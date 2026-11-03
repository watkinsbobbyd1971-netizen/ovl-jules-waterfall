import subprocess
import json
import sys

def run(cmd):
    return subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

try:
    # 2. Parse file and build description
    count = 0
    lines = []
    with open("output/profile-ACC_05/batch_03_CAT15_2010S_R06-10_v3.jsonl", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                count += 1
                record = json.loads(line)
                lines.append(f"{record['canonical_dedup_key']} | {record['verification_citation_url']}")

    desc = f"{count}\n" + "\n".join(lines)
    with open("pr_desc.txt", "w") as f:
        f.write(desc)

    title = f"[ACC_05] batch_03 CAT15_2010S_R06-10 ({count} verified blocks)"
    print(title)
    print(desc)

except Exception as e:
    print(f"Error: {e}")
    if isinstance(e, subprocess.CalledProcessError):
        print(e.stderr)
