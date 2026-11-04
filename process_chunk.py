import csv
import gzip
import urllib.request
import urllib.parse
import json
import time
import concurrent.futures

IN_FILE = "tasks/natural_event/chunk-0005.csv.gz"
OUT_CSV = "out/natural_event/chunk-0005.csv"
OUT_NOTES = "out/natural_event/chunk-0005.notes.txt"

def search_wikipedia_wikidata(subject_name):
    # This might match unrelated things if it's a descriptive event, but let's try wbsearchentities with strict checking

    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbsearchentities",
        "search": subject_name,
        "language": "en",
        "format": "json",
        "limit": 5
    })
    req = urllib.request.Request(url, headers={'User-Agent': 'CorpusPropertyFill/1.0 (test@example.com)'})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                search_results = data.get('search', [])
                if search_results:
                    for res in search_results:
                        # Ensure the label or one of the aliases is extremely close to the subject_name
                        label = res.get('label', '').lower()
                        aliases = [a.lower() for a in res.get('aliases', [])]
                        sn = subject_name.lower()

                        # We want exact or near exact matches.
                        # Sometimes subjects are "1986 Chalfant Valley Earthquake", label "1986 Chalfant Valley earthquake"
                        if label == sn or sn in aliases:
                            return res.get('id')
                return None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2)
                continue
        except Exception as e:
            time.sleep(1)
            continue
    return None

def query_wikidata_by_id(item_id):
    query = f"""
    SELECT ?prop ?propLabel ?val ?valLabel WHERE {{
      wd:{item_id} ?p ?val.
      ?prop wikibase:directClaim ?p.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT 100
    """
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({'query': query, 'format': 'json'})

    req = urllib.request.Request(url, headers={'User-Agent': 'CorpusPropertyFill/1.0 (test@example.com)'})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data.get('results', {}).get('bindings', [])
        except Exception as e:
            time.sleep(1)
            continue
    return []

PROP_MAP = {
    'duration': ['duration'],
    'location': ['country', 'location', 'coordinate location'],
    'magnitude_with_scale': ['earthquake magnitude on the Richter magnitude scale', 'earthquake magnitude on the moment magnitude scale'],
    'phenomenon_time': ['point in time', 'start time', 'end time', 'date of occurrence'],
    'event_type': ['instance of']
}

def extract_properties(bindings, item_id):
    extracted = []
    seen = set()
    subject_url = f"http://www.wikidata.org/entity/{item_id}"

    for b in bindings:
        prop_label = b.get('propLabel', {}).get('value', '').lower()
        val_label = b.get('valLabel', {}).get('value', '')

        if not prop_label or not val_label:
            continue

        for col, props in PROP_MAP.items():
            if prop_label in props:
                if (col, val_label) not in seen:
                    extracted.append((col, val_label, subject_url))
                    seen.add((col, val_label))

    return extracted

def process_row(row):
    key = row['canonical_dedup_key']
    subject = row['subject_name']
    item_id = search_wikipedia_wikidata(subject)
    rows_out = []
    if item_id:
        bindings = query_wikidata_by_id(item_id)
        props = extract_properties(bindings, item_id)
        for col, val, url in props:
            rows_out.append([key, col, val, url])
    return rows_out

def main():
    rows_with_data = []

    rows = []
    with gzip.open(IN_FILE, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_row, rows))
        for r in results:
            rows_with_data.extend(r)

    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        for row in rows_with_data:
            writer.writerow(row)

    if not rows_with_data:
        with open(OUT_NOTES, 'w', encoding='utf-8') as f:
            f.write("Attempted to find exact matches for subject names on Wikidata using the wbsearchentities API.\n")
            f.write("No exact matches were found for any subjects or they lacked relevant properties.\n")
    else:
        with open(OUT_NOTES, 'w', encoding='utf-8') as f:
            f.write("Attempted to find exact matches for subject names on Wikidata using the wbsearchentities API.\n")

if __name__ == '__main__':
    main()
