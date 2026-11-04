import csv
import gzip
import os
import json
import urllib.request
import urllib.parse
import concurrent.futures
import time

# Properties mapping
# component_relationship, descriptive_identity, dimension_length, identity_label, manufacturer_or_creator, mass, material_identity, model_identifier, operating_state, rated_power, variant_identifier

PROPERTY_MAP = {
    'P527': 'component_relationship', # has part
    'P31': 'descriptive_identity', # instance of
    'P279': 'descriptive_identity', # subclass of
    'P2043': 'dimension_length', # length
    'P176': 'manufacturer_or_creator', # manufacturer
    'P2067': 'mass', # mass
    'P186': 'material_identity', # material used
    'P2102': 'rated_power', # maximum power output
    # Add other mappings if necessary, though finding exact matches might be rare for everything
}

def search_wikidata(subject_name):
    query = subject_name
    # memory says we might need to strip model year, but let's try direct first
    url = 'https://www.wikidata.org/w/api.php?action=wbsearchentities&search=' + urllib.parse.quote(query) + '&language=en&format=json'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Bot for corpus fill)'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('search'):
                # We need an exact match in label or alias to be safe, to avoid ambiguous matches
                for item in data['search']:
                    if item.get('match', {}).get('text', '').lower() == query.lower() or item.get('label', '').lower() == query.lower():
                        return item['id']
    except Exception as e:
        pass
    return None

def get_wikidata_claims(entity_id):
    url = f'https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&language=en&format=json'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Bot for corpus fill)'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('entities', {}).get(entity_id, {}).get('claims', {})
    except Exception:
        return {}

def resolve_entity(entity_id):
    url = f'https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&language=en&format=json&props=labels'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Bot for corpus fill)'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('entities', {}).get(entity_id, {}).get('labels', {}).get('en', {}).get('value')
    except Exception:
        return None

def process_subject(row):
    key = row['canonical_dedup_key']
    subject = row['subject_name']

    # We should skip "Canonical" ones if they are not real subjects, but let's just search them and they will probably fail.
    entity_id = search_wikidata(subject)
    if not entity_id:
        return []

    claims = get_wikidata_claims(entity_id)
    results = []
    source_url = f"https://www.wikidata.org/wiki/{entity_id}"

    for prop_id, col_name in PROPERTY_MAP.items():
        if prop_id in claims:
            for claim in claims[prop_id]:
                mainsnak = claim.get('mainsnak', {})
                if mainsnak.get('snaktype') == 'value':
                    datavalue = mainsnak.get('datavalue', {})
                    if datavalue.get('type') == 'wikibase-entityid':
                        val_id = datavalue.get('value', {}).get('id')
                        val_label = resolve_entity(val_id)
                        if val_label:
                            results.append({
                                'canonical_dedup_key': key,
                                'column_name': col_name,
                                'value': json.dumps(val_label),
                                'source_url': source_url
                            })
                    elif datavalue.get('type') == 'quantity':
                        amount = datavalue.get('value', {}).get('amount')
                        if amount:
                            amount_val = float(amount)
                            # Handle units if needed. Memory says: convert units only by exact formula.
                            # Unit processing would go here
                            unit_url = datavalue.get('value', {}).get('unit')
                            if col_name == 'dimension_length':
                                if 'Q174728' in unit_url: # centimetre
                                    amount_val *= 10
                                elif 'Q11573' in unit_url: # metre
                                    amount_val *= 1000
                                elif 'Q174789' in unit_url: # millimetre
                                    pass
                                else:
                                    continue # Skip if unknown unit
                            elif col_name == 'mass':
                                if 'Q11570' in unit_url: # kilogram
                                    amount_val *= 1000
                                elif 'Q41803' in unit_url: # gram
                                    pass
                                elif 'Q6982035' in unit_url: # tonne
                                    amount_val *= 1000000
                                else:
                                    continue
                            elif col_name == 'rated_power':
                                if 'Q25236' in unit_url: # watt
                                    pass
                                elif 'Q3320608' in unit_url: # kilowatt
                                    amount_val *= 1000
                                elif 'Q164220' in unit_url: # horsepower
                                    amount_val *= 745.7
                                else:
                                    continue

                            results.append({
                                'canonical_dedup_key': key,
                                'column_name': col_name,
                                'value': str(amount_val), # Value shouldn't be JSON if it's a number? Actually COLUMNS.csv says dimension_length is JSON number. Actually, data_type JSON means we JSON encode it. Wait, number JSON encoded is just the number string.
                                'source_url': source_url
                            })
                    elif datavalue.get('type') == 'string':
                        val = datavalue.get('value')
                        results.append({
                            'canonical_dedup_key': key,
                            'column_name': col_name,
                            'value': json.dumps(val),
                            'source_url': source_url
                        })
    return results

def main():
    input_file = 'tasks/machinery/chunk-0006.csv.gz'
    output_dir = 'out/machinery'
    output_file = os.path.join(output_dir, 'chunk-0006.csv')
    notes_file = os.path.join(output_dir, 'chunk-0006.notes.txt')

    os.makedirs(output_dir, exist_ok=True)

    subjects = []
    with gzip.open(input_file, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects.append(row)

    # Remove subjects with "Canonical" as they look like metadata
    subjects = [s for s in subjects if "Canonical" not in s['subject_name']]

    all_results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_subject, row): row for row in subjects}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            if i % 50 == 0:
                print(f"Processed {i}/{len(subjects)}")
            try:
                res = future.result()
                all_results.extend(res)
            except Exception as e:
                pass

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        writer.writeheader()
        for res in all_results:
            writer.writerow(res)

    with open(notes_file, 'w', encoding='utf-8') as f:
        f.write("Queried Wikidata API for exact matches. Extracted properties P527, P31, P279, P2043, P176, P2067, P186, P2102 where available and units were known.\n")

if __name__ == '__main__':
    main()
