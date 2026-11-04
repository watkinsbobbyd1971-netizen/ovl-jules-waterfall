import urllib.parse
import json
import csv
import gzip
import time
import requests
from concurrent.futures import ThreadPoolExecutor
import threading
import sys
from collections import defaultdict
import os

WIKIDATA_SEARCH_API = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search={}&language=en&format=json"
WIKIDATA_GET_API = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids={}&languages=en&format=json"
USER_AGENT = "JulesCulturalBot/1.0 (test@test.com)"
HEADERS = {"User-Agent": USER_AGENT}

PROP_MAP = {
    'P31': 'descriptive_identity',
    'P279': 'descriptive_identity',
    'P170': 'creator_or_attribution',
    'P176': 'creator_or_attribution',
    'P571': 'date_or_interval',
    'P2043': 'dimension_length', # unit needs mm
    'P2067': 'mass', # unit needs g
    'P186': 'material_identity',
    'P217': 'collection_object_identifier',
    'P2079': 'technique',
}

def resolve_label(entity_id, resolved_labels):
    if entity_id in resolved_labels:
        return resolved_labels[entity_id]

    try:
        url = WIKIDATA_GET_API.format(entity_id)
        resp = requests.get(url, headers=HEADERS, timeout=5).json()
        label = resp.get('entities', {}).get(entity_id, {}).get('labels', {}).get('en', {}).get('value', None)
        if label:
            resolved_labels[entity_id] = label
            return label
    except:
        pass
    return None

def process_claim(claim, prop_id, resolved_labels):
    column = PROP_MAP.get(prop_id)
    if not column:
        return None

    try:
        datavalue = claim.get('mainsnak', {}).get('datavalue', {})
        if not datavalue:
            return None

        dtype = datavalue.get('type')
        val = datavalue.get('value')

        if dtype == 'wikibase-entityid':
            eid = val.get('id')
            label = resolve_label(eid, resolved_labels)
            if label:
                return (column, json.dumps(label))
        elif dtype == 'string':
            return (column, json.dumps(val))
        elif dtype == 'time':
            # try to get just the year or full time string
            time_str = val.get('time', '')
            if time_str.startswith('+'):
                time_str = time_str[1:]
            time_str = time_str.split('T')[0] # just date part roughly
            return (column, json.dumps(time_str))
        elif dtype == 'quantity':
            amount = val.get('amount', '0')
            if amount.startswith('+'):
                amount = amount[1:]
            amount = float(amount)
            unit_url = val.get('unit', '')
            unit_id = unit_url.split('/')[-1]

            # Unit conversions for mm and g
            # length P2043 in mm
            # mass P2067 in g
            if column == 'dimension_length':
                # Q174728 = cm, Q11573 = m, Q174789 = mm, Q218593 = inch, Q3710 = foot
                if unit_id == 'Q174789': # mm
                    pass
                elif unit_id == 'Q174728': # cm
                    amount *= 10
                elif unit_id == 'Q11573': # m
                    amount *= 1000
                elif unit_id == 'Q218593': # inch
                    amount *= 25.4
                elif unit_id == 'Q3710': # foot
                    amount *= 304.8
                else:
                    return None # Unhandled unit

                return (column, amount) # numbers are raw values without quotes in CSV unless JSON, wait COLUMNS says dimension_length is JSON?!
                # Let's check COLUMNS.csv for types: dimension_length is JSON, mass is JSON. Wait.
                # Actually, if it's JSON, a number is just `amount`? Or `str(amount)`? The instruction says JSON encoding.
                # We'll encode numbers as JSON strings as well, or just as JSON numbers (which are just the digits).

            elif column == 'mass':
                # Q41803 = g, Q11570 = kg, Q487056 = ton, Q100995 = pound, Q480798 = ounce
                if unit_id == 'Q41803': # g
                    pass
                elif unit_id == 'Q11570': # kg
                    amount *= 1000
                elif unit_id == 'Q100995': # pound
                    amount *= 453.592
                elif unit_id == 'Q480798': # ounce
                    amount *= 28.3495
                else:
                    return None # Unhandled unit

                return (column, amount)
    except:
        pass
    return None


def fetch_for_subject(dedup_key, subject_name):
    resolved_labels = {}
    results = []
    sources = set()

    try:
        url = WIKIDATA_SEARCH_API.format(urllib.parse.quote(subject_name))
        resp = requests.get(url, headers=HEADERS, timeout=10).json()
        sources.add(url)

        search_results = resp.get('search', [])
        matched_id = None
        for res in search_results:
            label = res.get('label', '')
            aliases = res.get('aliases', [])
            if label.lower() == subject_name.lower() or any(a.lower() == subject_name.lower() for a in aliases):
                matched_id = res['id']
                break

        if not matched_id:
            return results, sources

        entity_url = WIKIDATA_GET_API.format(matched_id)
        sources.add(entity_url)
        ent_resp = requests.get(entity_url, headers=HEADERS, timeout=10).json()
        claims = ent_resp.get('entities', {}).get(matched_id, {}).get('claims', {})

        source_url = f"https://www.wikidata.org/wiki/{matched_id}"

        for prop_id in PROP_MAP.keys():
            if prop_id in claims:
                for claim in claims[prop_id]:
                    # Some properties we just take the first claim
                    val = process_claim(claim, prop_id, resolved_labels)
                    if val:
                        column, value = val
                        if isinstance(value, float):
                            # format numbers to general form
                            # value = json.dumps(value)
                            # If it's an integer we can keep it without .0
                            if value.is_integer():
                                value = int(value)
                            value = json.dumps(value)

                        results.append({
                            'canonical_dedup_key': dedup_key,
                            'column_name': column,
                            'value': value,
                            'source_url': source_url
                        })

    except Exception as e:
        print(f"Error fetching {subject_name}: {e}")

    return results, sources


def main():
    input_file = "tasks/cultural_object/chunk-0009.csv.gz"
    out_dir = "out/cultural_object"
    os.makedirs(out_dir, exist_ok=True)
    out_csv = os.path.join(out_dir, "chunk-0009.csv")
    out_notes = os.path.join(out_dir, "chunk-0009.notes.txt")

    rows = []
    with gzip.open(input_file, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    results = []
    all_sources = set()

    def process_row(row):
        key = row['canonical_dedup_key']
        name = row['subject_name']
        res, src = fetch_for_subject(key, name)
        return res, src

    print(f"Processing {len(rows)} items...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for row in rows:
            futures.append(executor.submit(process_row, row))

        for i, future in enumerate(futures):
            res, src = future.result()
            results.extend(res)
            all_sources.update(src)
            if (i+1) % 50 == 0:
                print(f"Processed {i+1}/{len(rows)}")

    # Write output
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    with open(out_notes, 'w', encoding='utf-8') as f:
        f.write("Queried Wikidata APIs for properties:\n")
        f.write("P31, P279, P170, P176, P571, P2043, P2067, P186, P217, P2079\n\n")
        f.write("Sources:\n")
        for src in sorted(list(all_sources)):
            f.write(src + "\n")

    print("Done!")

if __name__ == '__main__':
    main()
