import urllib.request
import urllib.parse
import json
import gzip
import csv
import os
import concurrent.futures
import time

def get_label(entity_id, cache):
    if entity_id in cache:
        return cache[entity_id]
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&props=labels&languages=en&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if 'entities' in data and entity_id in data['entities'] and 'labels' in data['entities'][entity_id] and 'en' in data['entities'][entity_id]['labels']:
                label = data['entities'][entity_id]['labels']['en']['value']
                cache[entity_id] = label
                return label
    except Exception:
        pass
    return None

def process_subject(item_tuple):
    canonical_key, subject_name = item_tuple

    search_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(subject_name)}&language=en&format=json"
    req = urllib.request.Request(search_url, headers={'User-Agent': 'MyBot/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            search_data = json.loads(response.read().decode())
    except Exception:
        return []

    if not search_data.get('search'):
        return []

    results = []
    for item in search_data['search']:
        match_text = item.get('match', {}).get('text', '').lower()
        label_text = item.get('label', '').lower()
        if match_text == subject_name.lower() or label_text == subject_name.lower():
            entity_id = item['id']

            # Fetch entity properties
            entity_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json"
            req2 = urllib.request.Request(entity_url, headers={'User-Agent': 'MyBot/1.0'})
            try:
                with urllib.request.urlopen(req2) as response:
                    entity_data = json.loads(response.read().decode())
            except Exception:
                continue

            if 'entities' in entity_data and entity_id in entity_data['entities']:
                claims = entity_data['entities'][entity_id].get('claims', {})
                source_url = f"https://www.wikidata.org/wiki/{entity_id}"

                # We need to resolve labels for Q-IDs later, so we yield raw tuples and resolve them in the main thread
                # P176 / P170 -> creator_or_attribution
                for prop_id in ['P176', 'P170']:
                    if prop_id in claims:
                        for claim in claims[prop_id]:
                            if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'wikibase-entityid':
                                val_id = claim['mainsnak']['datavalue']['value']['id']
                                results.append((canonical_key, 'creator_or_attribution', val_id, source_url, 'string_resolve'))

                # P31 -> descriptive_identity
                if 'P31' in claims:
                    for claim in claims['P31']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'wikibase-entityid':
                            val_id = claim['mainsnak']['datavalue']['value']['id']
                            results.append((canonical_key, 'descriptive_identity', val_id, source_url, 'string_resolve'))

                # P186 -> material_identity
                if 'P186' in claims:
                    for claim in claims['P186']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'wikibase-entityid':
                            val_id = claim['mainsnak']['datavalue']['value']['id']
                            results.append((canonical_key, 'material_identity', val_id, source_url, 'string_resolve'))

                # P366 -> historical_function
                if 'P366' in claims:
                    for claim in claims['P366']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'wikibase-entityid':
                            val_id = claim['mainsnak']['datavalue']['value']['id']
                            results.append((canonical_key, 'historical_function', val_id, source_url, 'string_resolve'))

                # P571 -> date_or_interval
                if 'P571' in claims:
                    for claim in claims['P571']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'time':
                            time_val = claim['mainsnak']['datavalue']['value']['time']
                            results.append((canonical_key, 'date_or_interval', time_val, source_url, 'string'))

                # P2067 -> mass (g)
                if 'P2067' in claims:
                    for claim in claims['P2067']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'quantity':
                            amount = claim['mainsnak']['datavalue']['value']['amount']
                            unit = claim['mainsnak']['datavalue']['value']['unit']
                            try:
                                amount = float(amount.strip('+'))
                                if 'Q41803' in unit: # gram
                                    val = amount
                                elif 'Q11570' in unit: # kilogram
                                    val = amount * 1000
                                elif 'Q48013' in unit: # ounce
                                    val = amount * 28.3495
                                elif 'Q100995' in unit: # pound
                                    val = amount * 453.592
                                else:
                                    val = amount # Default, might be wrong but we output anyway
                                results.append((canonical_key, 'mass', str(val), source_url, 'number'))
                            except ValueError:
                                pass

                # P2043 -> dimension_length (mm)
                if 'P2043' in claims:
                    for claim in claims['P2043']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'quantity':
                            amount = claim['mainsnak']['datavalue']['value']['amount']
                            unit = claim['mainsnak']['datavalue']['value']['unit']
                            try:
                                amount = float(amount.strip('+'))
                                if 'Q174789' in unit: # millimeter
                                    val = amount
                                elif 'Q174728' in unit: # centimeter
                                    val = amount * 10
                                elif 'Q11573' in unit: # meter
                                    val = amount * 1000
                                elif 'Q218593' in unit: # inch
                                    val = amount * 25.4
                                elif 'Q3710' in unit: # foot
                                    val = amount * 304.8
                                else:
                                    val = amount
                                results.append((canonical_key, 'dimension_length', str(val), source_url, 'number'))
                            except ValueError:
                                pass

            break # Only take the first exact match

    time.sleep(0.01)
    return results

def main():
    input_file = "tasks/historical_protective/chunk-0006.csv.gz"
    out_dir = "out/historical_protective"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "chunk-0006.csv")

    subjects = []
    with gzip.open(input_file, "rt") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            subjects.append((row[0], row[1]))

    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_subject, s): s for s in subjects}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                all_results.extend(res)

    label_cache = {}

    with open(out_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])

        for key, col, val, src, val_type in all_results:
            if val_type == 'string_resolve':
                resolved = get_label(val, label_cache)
                if resolved:
                    # properly encode json string in CSV (needs to be e.g. "\"value\"")
                    # using json.dumps returns a string with quotes, e.g. '"value"'
                    json_val = json.dumps(resolved)
                    writer.writerow([key, col, json_val, src])
            elif val_type == 'string':
                json_val = json.dumps(val)
                writer.writerow([key, col, json_val, src])
            elif val_type == 'number':
                # numbers don't need quotes in JSON
                writer.writerow([key, col, val, src])

if __name__ == "__main__":
    main()
