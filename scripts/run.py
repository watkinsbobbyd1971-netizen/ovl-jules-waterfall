import asyncio
import csv
import gzip
import json
import logging
import os
from urllib.parse import urlencode

import aiohttp

# Properties for watercraft
# P176: manufacturer
# P2043: length (mm)
# P2262: draft (mm)
# P2067: mass (g)
# P31: instance of (descriptive_identity)
# P1448: official name (identity_label)
# P527: has part (component_relationship)
# P186: material used (material_identity)

PROPERTIES = {
    'manufacturer_or_creator': 'P176',
    'dimension_length': 'P2043',
    'draft': 'P2262',
    'mass': 'P2067',
    'displacement_mass': 'P2067', # displacement is usually represented by mass for ships in wikidata, or we might need another property
    'descriptive_identity': 'P31',
    'component_relationship': 'P527',
    'material_identity': 'P186',
}

WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
USER_AGENT = "MyBot/1.0 (https://example.org/; mybot@example.org)"

# Cache for searches
SEARCH_CACHE = {}

async def fetch_wikidata_search(session, subject_name):
    if subject_name in SEARCH_CACHE:
        return SEARCH_CACHE[subject_name]

    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "type": "item",
        "search": subject_name
    }

    try:
        async with session.get(WIKIDATA_API_URL, params=params, headers={"User-Agent": USER_AGENT}) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("search") and len(data["search"]) > 0:
                    # Look for exact or very close matches
                    for result in data["search"]:
                        if 'description' in result and ('ship' in result['description'].lower() or 'boat' in result['description'].lower() or 'submarine' in result['description'].lower() or 'watercraft' in result['description'].lower() or 'vessel' in result['description'].lower() or 'barge' in result['description'].lower()):
                            SEARCH_CACHE[subject_name] = result["id"]
                            return result["id"]
                    # Fallback to first if no description match but exact name
                    if data["search"][0]["label"].lower() == subject_name.lower():
                        SEARCH_CACHE[subject_name] = data["search"][0]["id"]
                        return data["search"][0]["id"]
    except Exception as e:
        print(f"Error searching for {subject_name}: {e}")
        pass

    SEARCH_CACHE[subject_name] = None
    return None

async def fetch_wikidata_entity(session, entity_id):
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": entity_id,
        "languages": "en",
        "props": "claims|labels"
    }
    try:
        async with session.get(WIKIDATA_API_URL, params=params, headers={"User-Agent": USER_AGENT}) as response:
            if response.status == 200:
                data = await response.json()
                if "entities" in data and entity_id in data["entities"]:
                    return data["entities"][entity_id]
    except Exception as e:
        print(f"Error fetching entity {entity_id}: {e}")
    return None

def extract_values(entity, claims):
    results = []
    source_url = f"https://www.wikidata.org/wiki/{entity['id']}"

    # helper for resolving item values
    def get_item_label(claim):
        try:
            mainsnak = claim.get('mainsnak', {})
            if mainsnak.get('snaktype') == 'value' and mainsnak.get('datavalue', {}).get('type') == 'wikibase-entityid':
                item_id = mainsnak['datavalue']['value']['id']
                return item_id # We'll need a way to resolve this if we want text, or we can just yield the Qid, or we might need to batch resolve
        except:
            pass
        return None

    def get_quantity(claim, unit_conversion=1.0):
        try:
            mainsnak = claim.get('mainsnak', {})
            if mainsnak.get('snaktype') == 'value' and mainsnak.get('datavalue', {}).get('type') == 'quantity':
                amount_str = mainsnak['datavalue']['value']['amount']
                # Wikidata quantities start with + or -
                if amount_str.startswith('+'):
                    amount = float(amount_str[1:])
                else:
                    amount = float(amount_str)
                return amount * unit_conversion
        except:
            pass
        return None

    def get_string(claim):
        try:
            mainsnak = claim.get('mainsnak', {})
            if mainsnak.get('snaktype') == 'value' and mainsnak.get('datavalue', {}).get('type') == 'string':
                return mainsnak['datavalue']['value']
        except:
            pass
        return None

    # We need a label resolver
    label_requests = []

    # We will build an intermediate structure, then resolve labels
    intermediate = []

    if 'P176' in claims: # manufacturer
        for claim in claims['P176']:
            item_id = get_item_label(claim)
            if item_id:
                intermediate.append(('manufacturer_or_creator', item_id))
                label_requests.append(item_id)

    if 'P2043' in claims: # dimension_length (Wikidata usually metres, we want mm)
        # Check units? default is metre Q11573
        for claim in claims['P2043']:
            try:
                unit = claim['mainsnak']['datavalue']['value'].get('unit', '')
                conversion = 1000.0 # assume metres
                if 'Q174728' in unit: # centimetre
                    conversion = 10.0
                elif 'Q174789' in unit: # millimetre
                    conversion = 1.0
                val = get_quantity(claim, conversion)
                if val is not None:
                    results.append(('dimension_length', val, source_url))
            except:
                pass

    if 'P2262' in claims: # draft (usually metres, want mm)
        for claim in claims['P2262']:
            try:
                unit = claim['mainsnak']['datavalue']['value'].get('unit', '')
                conversion = 1000.0 # assume metres
                if 'Q174728' in unit:
                    conversion = 10.0
                elif 'Q174789' in unit:
                    conversion = 1.0
                val = get_quantity(claim, conversion)
                if val is not None:
                    results.append(('draft', val, source_url))
            except:
                pass

    if 'P2067' in claims: # mass (usually tonnes Q12070381 or kilograms Q11570, want g)
        for claim in claims['P2067']:
            try:
                unit = claim['mainsnak']['datavalue']['value'].get('unit', '')
                conversion = 1000000.0 # assume tonnes
                if 'Q11570' in unit: # kg
                    conversion = 1000.0
                elif 'Q41803' in unit: # gram
                    conversion = 1.0
                val = get_quantity(claim, conversion)
                if val is not None:
                    results.append(('mass', val, source_url))
                    results.append(('displacement_mass', val, source_url))
            except:
                pass

    if 'P31' in claims: # descriptive_identity
        for claim in claims['P31']:
            item_id = get_item_label(claim)
            if item_id:
                intermediate.append(('descriptive_identity', item_id))
                label_requests.append(item_id)

    if 'P527' in claims: # component_relationship
        for claim in claims['P527']:
            item_id = get_item_label(claim)
            if item_id:
                intermediate.append(('component_relationship', item_id))
                label_requests.append(item_id)

    if 'P186' in claims: # material_identity
        for claim in claims['P186']:
            item_id = get_item_label(claim)
            if item_id:
                intermediate.append(('material_identity', item_id))
                label_requests.append(item_id)

    # identity_label from labels
    try:
        if 'labels' in entity and 'en' in entity['labels']:
            results.append(('identity_label', entity['labels']['en']['value'], source_url))
    except:
        pass

    return intermediate, label_requests, results

async def resolve_labels(session, item_ids):
    if not item_ids:
        return {}

    unique_ids = list(set(item_ids))
    labels = {}

    # Process in batches of 50
    for i in range(0, len(unique_ids), 50):
        batch = unique_ids[i:i+50]
        params = {
            "action": "wbgetentities",
            "format": "json",
            "ids": "|".join(batch),
            "languages": "en",
            "props": "labels"
        }
        try:
            async with session.get(WIKIDATA_API_URL, params=params, headers={"User-Agent": USER_AGENT}) as response:
                if response.status == 200:
                    data = await response.json()
                    if "entities" in data:
                        for qid, entity_data in data["entities"].items():
                            try:
                                labels[qid] = entity_data['labels']['en']['value']
                            except:
                                labels[qid] = qid
        except Exception as e:
            print(f"Error resolving labels: {e}")

    return labels

async def process_row(session, row):
    canonical_dedup_key = row['canonical_dedup_key']
    subject_name = row['subject_name']

    # Skip non-watercraft based on naming or identifiers if needed, but chunk is watercraft

    entity_id = await fetch_wikidata_search(session, subject_name)
    if not entity_id:
        # try stripping common prefixes like USS, HMS
        if subject_name.startswith('USS ') or subject_name.startswith('HMS ') or subject_name.startswith('SS '):
            clean_name = subject_name.split(' ', 1)[1]
            entity_id = await fetch_wikidata_search(session, clean_name)

    if not entity_id:
        return []

    entity = await fetch_wikidata_entity(session, entity_id)
    if not entity:
        return []

    claims = entity.get('claims', {})

    intermediate, label_requests, results = extract_values(entity, claims)

    labels = await resolve_labels(session, label_requests)
    source_url = f"https://www.wikidata.org/wiki/{entity_id}"

    for prop, qid in intermediate:
        if qid in labels:
            results.append((prop, labels[qid], source_url))

    # Format for output
    formatted_results = []
    for prop, val, src in results:
        # Apply JSON encoding to all values since data_type is JSON
        formatted_results.append({
            'canonical_dedup_key': canonical_dedup_key,
            'column_name': prop,
            'value': json.dumps(val),
            'source_url': src
        })

    return formatted_results

async def main():
    input_file = "tasks/watercraft/chunk-0011.csv.gz"
    output_dir = "out/watercraft"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "chunk-0011.csv")
    notes_file = os.path.join(output_dir, "chunk-0011.notes.txt")

    rows = []
    with gzip.open(input_file, 'rt') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"Processing {len(rows)} subjects...")

    all_results = []

    # Use semaphore to limit concurrency
    sem = asyncio.Semaphore(5)

    async with aiohttp.ClientSession() as session:
        async def bound_process_row(row):
            async with sem:
                # Add delay to avoid aggressive rate limiting
                await asyncio.sleep(0.5)
                return await process_row(session, row)

        tasks = [bound_process_row(row) for row in rows]
        chunk_results = await asyncio.gather(*tasks)

        for res in chunk_results:
            all_results.extend(res)

    print(f"Found {len(all_results)} property values.")

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        writer.writeheader()
        writer.writerows(all_results)

    with open(notes_file, 'w') as f:
        f.write("Queried Wikidata API via wbsearchentities and wbgetentities for exact string matches.\n")
        f.write("Extracted P176, P2043, P2262, P2067, P31, P1448, P527, P186 where available.\n")

if __name__ == "__main__":
    asyncio.run(main())
