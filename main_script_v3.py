import asyncio
import aiohttp
import csv
import gzip
import json
import urllib.parse
import sys
import re

def strip_year(subject_name):
    return re.sub(r'\s+\d{4}$', '', subject_name)

def extract_make(subject_name):
    if subject_name.startswith("Harley-Davidson"):
        return "Harley-Davidson"
    if subject_name.startswith("Honda"):
        return "Honda"
    return None

async def wikidata_search(session, search_term):
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(search_term)}&language=en&format=json"
    headers = {"User-Agent": "JulesBot/1.0"}
    try:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            if data.get('search'):
                # Try exact match first
                for r in data['search']:
                    if r.get('label', '').lower() == search_term.lower():
                        return r['id']
                return data['search'][0]['id']
    except:
        pass
    return None

async def wiki_api_search(session, search_term):
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(search_term)}&utf8=&format=json"
    headers = {"User-Agent": "JulesBot/1.0"}
    try:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            if 'query' in data and 'search' in data['query'] and data['query']['search']:
                return data['query']['search'][0]['title']
    except:
        pass
    return None

async def wikidata_get_entity_by_title(session, title):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={urllib.parse.quote(title)}&format=json"
    headers = {"User-Agent": "JulesBot/1.0"}
    try:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            if 'entities' in data:
                for qid in data['entities']:
                    if qid != "-1":
                        return qid
    except:
        pass
    return None

async def wikidata_get_claims(session, qid):
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    headers = {"User-Agent": "JulesBot/1.0"}
    try:
        async with session.get(url, headers=headers) as resp:
            data = await resp.json()
            if 'entities' in data and qid in data['entities']:
                return data['entities'][qid].get('claims', {})
    except:
        pass
    return {}

async def process_subject(session, key, subject, cache):
    make = extract_make(subject)
    results = []

    if make == "Harley-Davidson":
        make_qid = "Q23208"
        make_url = "https://www.wikidata.org/wiki/Q23208"
    elif make == "Honda":
        make_qid = "Q9584"
        make_url = "https://www.wikidata.org/wiki/Q9584"
    else:
        make_url = None

    if make_url:
        results.append({
            'canonical_dedup_key': key,
            'column_name': 'manufacturer_or_creator',
            'value': json.dumps(make),
            'source_url': make_url
        })

    term_no_year = strip_year(subject)

    if term_no_year in cache:
        qid = cache[term_no_year]
    else:
        qid = await wikidata_search(session, term_no_year)
        if not qid:
            title = await wiki_api_search(session, term_no_year)
            if title:
                qid = await wikidata_get_entity_by_title(session, title)
        cache[term_no_year] = qid

    if not qid:
        return results

    claims = await wikidata_get_claims(session, qid)
    source_url = f"https://www.wikidata.org/wiki/{qid}"

    # Mass P2067
    if 'P2067' in claims:
        for claim in claims['P2067']:
            if claim['mainsnak']['snaktype'] == 'value':
                val = claim['mainsnak']['datavalue']['value']
                amount = float(val['amount'])
                unit_qid = val['unit'].split('/')[-1] if val['unit'] != '1' else None
                if unit_qid == 'Q11570': # kg
                    results.append({
                        'canonical_dedup_key': key,
                        'column_name': 'mass',
                        'value': json.dumps(amount * 1000),
                        'source_url': source_url
                    })
                    break
                elif unit_qid == 'Q41803': # g
                    results.append({
                        'canonical_dedup_key': key,
                        'column_name': 'mass',
                        'value': json.dumps(amount),
                        'source_url': source_url
                    })
                    break

    # length P2043
    if 'P2043' in claims:
        for claim in claims['P2043']:
            if claim['mainsnak']['snaktype'] == 'value':
                val = claim['mainsnak']['datavalue']['value']
                amount = float(val['amount'])
                unit_qid = val['unit'].split('/')[-1] if val['unit'] != '1' else None
                if unit_qid == 'Q11573': # m
                    results.append({
                        'canonical_dedup_key': key,
                        'column_name': 'dimension_length',
                        'value': json.dumps(amount * 1000),
                        'source_url': source_url
                    })
                    break
                elif unit_qid == 'Q174789': # mm
                    results.append({
                        'canonical_dedup_key': key,
                        'column_name': 'dimension_length',
                        'value': json.dumps(amount),
                        'source_url': source_url
                    })
                    break

    return results

async def main():
    filename = 'tasks/cycle_cart/chunk-0007.csv.gz'
    subjects = []
    with gzip.open(filename, 'rt') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects.append((row['canonical_dedup_key'], row['subject_name']))

    print(f"Loaded {len(subjects)} subjects")
    cache = {}

    all_results = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        for key, subject in subjects:
            tasks.append(process_subject(session, key, subject, cache))

            if len(tasks) >= 50:
                res = await asyncio.gather(*tasks)
                for r in res:
                    all_results.extend(r)
                tasks = []
                await asyncio.sleep(0.5)

        if tasks:
            res = await asyncio.gather(*tasks)
            for r in res:
                all_results.extend(r)

    out_file = 'out/cycle_cart/chunk-0007.csv'
    with open(out_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        writer.writeheader()
        writer.writerows(all_results)

    print(f"Wrote {len(all_results)} rows to {out_file}")

if __name__ == '__main__':
    asyncio.run(main())
