import csv
import gzip
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

INPUT_FILE = "tasks/fungal_microbe/chunk-0012.csv.gz"

def fetch_gbif(subject_name):
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(subject_name)}&strict=true"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('matchType') == 'EXACT':
                return data
    except Exception as e:
        print(f"Error fetching {subject_name}: {e}")
    return None

def fetch_details(usage_key):
    url = f"https://api.gbif.org/v1/species/{usage_key}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching details {usage_key}: {e}")
    return None

with gzip.open(INPUT_FILE, 'rt', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)[:10]

for row in rows:
    subject = row['subject_name']
    match = fetch_gbif(subject)
    if match:
        print(f"Match for {subject}: {match.get('canonicalName')}")
        details = fetch_details(match['usageKey'])
        if details:
            print(f"  Authorship: {details.get('authorship')}")

        ranks = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus']
        desc = [match[r] for r in ranks if r in match]
        print(f"  Desc: {desc}")
