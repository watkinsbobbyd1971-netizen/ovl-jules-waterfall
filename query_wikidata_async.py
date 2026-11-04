import csv
import gzip
import json
import os
import asyncio
import aiohttp
import urllib.parse

INPUT_FILE = 'tasks/built_environment/chunk-0004.csv.gz'
OUTPUT_DIR = 'out/built_environment'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'chunk-0004.csv')
NOTES_FILE = os.path.join(OUTPUT_DIR, 'chunk-0004.notes.txt')

os.makedirs(OUTPUT_DIR, exist_ok=True)

USER_AGENT = 'CoolBot/1.0 (contact: coolbot@example.com)'
HEADERS = {'User-Agent': USER_AGENT}

# Limit concurrency to respect wikidata rate limits
SEMAPHORE = asyncio.Semaphore(5)

async def search_wikidata(session, subject_name):
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(subject_name)}&language=en&format=json"
    try:
        async with SEMAPHORE:
            async with session.get(url, headers=HEADERS, timeout=10) as response:
                data = await response.json()
        if data.get('search'):
            for item in data['search']:
                if item.get('match', {}).get('text', '').lower() == subject_name.lower():
                    return item['id']
                if item.get('label', '').lower() == subject_name.lower():
                    return item['id']
    except Exception as e:
        pass
    return None

async def get_entity_data(session, entity_id):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&props=claims|labels&languages=en&format=json"
    try:
        async with SEMAPHORE:
            async with session.get(url, headers=HEADERS, timeout=10) as response:
                data = await response.json()
        return data.get('entities', {}).get(entity_id, {})
    except Exception:
        return {}

async def get_label(session, entity_id):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&props=labels&languages=en&format=json"
    try:
        async with SEMAPHORE:
            async with session.get(url, headers=HEADERS, timeout=10) as response:
                data = await response.json()
        return data.get('entities', {}).get(entity_id, {}).get('labels', {}).get('en', {}).get('value')
    except Exception:
        return None

async def process_subject(session, row):
    key = row['canonical_dedup_key']
    name = row['subject_name']

    entity_id = await search_wikidata(session, name)
    if not entity_id:
        return []

    data = await get_entity_data(session, entity_id)
    if not data:
        return []

    results = []

    label = data.get('labels', {}).get('en', {}).get('value')
    if label:
        results.append({
            'key': key,
            'col': 'identity_label',
            'val': json.dumps(label),
            'url': f"https://www.wikidata.org/wiki/{entity_id}"
        })

    claims = data.get('claims', {})

    if 'P31' in claims:
        for claim in claims['P31']:
            mainsnak = claim.get('mainsnak', {})
            if mainsnak.get('datatype') == 'wikibase-item' and mainsnak.get('datavalue'):
                val_id = mainsnak['datavalue']['value']['id']
                val_label = await get_label(session, val_id)
                if val_label:
                    results.append({
                        'key': key,
                        'col': 'descriptive_identity',
                        'val': json.dumps(val_label),
                        'url': f"https://www.wikidata.org/wiki/{entity_id}"
                    })
                    break

    if 'P571' in claims:
        for claim in claims['P571']:
            mainsnak = claim.get('mainsnak', {})
            if mainsnak.get('datatype') == 'time' and mainsnak.get('datavalue'):
                time_str = mainsnak['datavalue']['value']['time']
                year = time_str.split('-')[0].replace('+', '')
                results.append({
                    'key': key,
                    'col': 'construction_date',
                    'val': json.dumps(year),
                    'url': f"https://www.wikidata.org/wiki/{entity_id}"
                })
                break

    if 'P17' in claims:
        for claim in claims['P17']:
            mainsnak = claim.get('mainsnak', {})
            if mainsnak.get('datatype') == 'wikibase-item' and mainsnak.get('datavalue'):
                val_id = mainsnak['datavalue']['value']['id']
                val_label = await get_label(session, val_id)
                if val_label:
                    results.append({
                        'key': key,
                        'col': 'location',
                        'val': json.dumps(val_label),
                        'url': f"https://www.wikidata.org/wiki/{entity_id}"
                    })
                    break

    return results

async def main_async():
    rows = []
    with gzip.open(INPUT_FILE, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"Total rows: {len(rows)}")

    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [process_subject(session, row) for row in rows]
        # Run in chunks to print progress
        chunk_size = 50
        for i in range(0, len(tasks), chunk_size):
            print(f"Processing chunk {i//chunk_size + 1}/{len(tasks)//chunk_size + 1}...")
            chunk_tasks = tasks[i:i+chunk_size]
            chunk_results = await asyncio.gather(*chunk_tasks)
            for res in chunk_results:
                if res:
                    results.extend(res)
            # Add a small delay between chunks to be safe with rate limits
            await asyncio.sleep(1)

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        for r in results:
            writer.writerow([r['key'], r['col'], r['val'], r['url']])

    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        f.write("Queried Wikidata API (wbsearchentities, wbgetentities) for subjects, found exact matches.\n")

if __name__ == '__main__':
    asyncio.run(main_async())
