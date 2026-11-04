import asyncio
import aiohttp
import csv
import gzip
import json
import urllib.parse
import sys

# P176 = manufacturer
# P2043 = dimension_length
# P2067 = mass
# P31 = descriptive_identity (instance of)
# P279 = subclass of

# We will try to fetch properties for each subject.
# Subjects are mostly motorcycles, e.g., "Harley-Davidson Dyna Super Glide Police 2004"

# We should strip the year at the end to search Wikidata, but we might want to keep it.
# Actually, Wikidata often just has the base model.
import re

def strip_year(subject_name):
    return re.sub(r'\s+\d{4}$', '', subject_name)

async def fetch_wikidata(session, subject, cache):
    search_term = strip_year(subject)
    if search_term in cache:
        return cache[search_term]

    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(search_term)}&language=en&format=json"

    headers = {"User-Agent": "JulesBot/1.0 (jules@example.com) python-requests/2.25.1"}
    try:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            if data.get('search') and len(data['search']) > 0:
                # get exact match or first match? Let's check exact match
                for result in data['search']:
                    if result['label'].lower() == search_term.lower():
                        cache[search_term] = result['id']
                        return result['id']
                cache[search_term] = data['search'][0]['id']
                return data['search'][0]['id']
            else:
                cache[search_term] = None
                return None
    except Exception as e:
        cache[search_term] = None
        return None

async def fetch_entity(session, qid, entity_cache):
    if qid in entity_cache:
        return entity_cache[qid]

    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    headers = {"User-Agent": "JulesBot/1.0 (jules@example.com) python-requests/2.25.1"}
    try:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            if 'entities' in data and qid in data['entities']:
                entity_cache[qid] = data['entities'][qid]
                return entity_cache[qid]
    except Exception as e:
        pass
    entity_cache[qid] = None
    return None

async def fetch_label(session, qid, label_cache):
    if qid in label_cache:
        return label_cache[qid]
    entity = await fetch_entity(session, qid, label_cache) # use same cache for full entity? No, keep it simple
    return None

def get_label(entity):
    try:
        return entity['labels']['en']['value']
    except:
        return None

async def process_chunk(filename):
    subjects = []
    with gzip.open(filename, 'rt') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects.append((row['canonical_dedup_key'], row['subject_name']))

    print(f"Loaded {len(subjects)} subjects")

    cache = {}
    entity_cache = {}

    results = []

    # We will just fetch English labels for P176 (manufacturer), P2067 (mass in kg, convert to g), P2043 (length in mm)

    async with aiohttp.ClientSession() as session:
        for idx, (key, subject) in enumerate(subjects):
            if idx % 100 == 0:
                print(f"Processed {idx}")

            qid = await fetch_wikidata(session, subject, cache)
            if not qid:
                continue

            entity = await fetch_entity(session, qid, entity_cache)
            if not entity:
                continue

            claims = entity.get('claims', {})
            source_url = f"https://www.wikidata.org/wiki/{qid}"

            # Manufacturer
            if 'P176' in claims:
                for claim in claims['P176']:
                    if claim['mainsnak']['snaktype'] == 'value':
                        m_qid = claim['mainsnak']['datavalue']['value']['id']
                        m_entity = await fetch_entity(session, m_qid, entity_cache)
                        if m_entity:
                            m_label = get_label(m_entity)
                            if m_label:
                                results.append({
                                    'canonical_dedup_key': key,
                                    'column_name': 'manufacturer_or_creator',
                                    'value': json.dumps(m_label),
                                    'source_url': source_url
                                })
                                break # just take first manufacturer

            # Mass
            if 'P2067' in claims:
                for claim in claims['P2067']:
                    if claim['mainsnak']['snaktype'] == 'value':
                        val = claim['mainsnak']['datavalue']['value']
                        amount = float(val['amount'])
                        unit_qid = val['unit'].split('/')[-1] if val['unit'] != '1' else None

                        # Q11570 is kilogram (kg) -> g
                        # Q41803 is gram (g) -> g
                        if unit_qid == 'Q11570':
                            amount_g = amount * 1000
                            results.append({
                                'canonical_dedup_key': key,
                                'column_name': 'mass',
                                'value': json.dumps(amount_g),
                                'source_url': source_url
                            })
                            break
                        elif unit_qid == 'Q41803':
                            results.append({
                                'canonical_dedup_key': key,
                                'column_name': 'mass',
                                'value': json.dumps(amount),
                                'source_url': source_url
                            })
                            break

            # length
            if 'P2043' in claims:
                for claim in claims['P2043']:
                    if claim['mainsnak']['snaktype'] == 'value':
                        val = claim['mainsnak']['datavalue']['value']
                        amount = float(val['amount'])
                        unit_qid = val['unit'].split('/')[-1] if val['unit'] != '1' else None

                        # Q11573 is metre (m) -> mm
                        # Q174789 is millimetre (mm) -> mm
                        if unit_qid == 'Q11573':
                            amount_mm = amount * 1000
                            results.append({
                                'canonical_dedup_key': key,
                                'column_name': 'dimension_length',
                                'value': json.dumps(amount_mm),
                                'source_url': source_url
                            })
                            break
                        elif unit_qid == 'Q174789':
                            results.append({
                                'canonical_dedup_key': key,
                                'column_name': 'dimension_length',
                                'value': json.dumps(amount),
                                'source_url': source_url
                            })
                            break

    print(f"Found {len(results)} properties")
    with open('out/cycle_cart/chunk-0007.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        writer.writeheader()
        writer.writerows(results)

if __name__ == '__main__':
    asyncio.run(process_chunk('tasks/cycle_cart/chunk-0007.csv.gz'))
