import gzip
import csv
import json
import urllib.request
import urllib.parse
import time
import uuid

def search_wikidata(q):
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(q)}&language=en&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            for match in data.get('search', []):
                # Check for exact match in label or aliases
                if match.get('label', '').lower() == q.lower() or q.lower() in [a.lower() for a in match.get('aliases', [])]:
                    if match.get('id'):
                        return match['id']
    except Exception as e:
        pass
    return None

def search_wikipedia_title(title):
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(title)}&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data['query']['search']:
                for res in data['query']['search']:
                    if res['title'].lower() == title.lower():
                        return res['title']
                return data['query']['search'][0]['title']
    except Exception as e:
        pass
    return None

def get_wikidata_id(title):
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&titles={urllib.parse.quote(title)}&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            pages = data['query']['pages']
            for page_id in pages:
                if 'pageprops' in pages[page_id] and 'wikibase_item' in pages[page_id]['pageprops']:
                    return pages[page_id]['pageprops']['wikibase_item']
    except Exception as e:
        pass
    return None

def get_wikidata_item(qid):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={qid}&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data['entities'][qid]
    except Exception as e:
        pass
    return None

def resolve_claim(claim_val):
    if claim_val['type'] == 'wikibase-entityid':
        return claim_val['value']['id']
    elif claim_val['type'] == 'string':
        return claim_val['value']
    elif claim_val['type'] == 'quantity':
        return float(claim_val['value']['amount'])
    elif claim_val['type'] == 'monolingualtext':
        return claim_val['value']['text']
    return None

def get_label(qid):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={qid}&format=json&props=labels"
    req = urllib.request.Request(url, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data['entities'][qid]['labels'].get('en', {}).get('value', qid)
    except Exception as e:
        pass
    return qid

PROP_MAP = {
    'component_relationship': ['P527'],
    'creator_or_attribution': ['P170', 'P84', 'P193', 'P631'],
    'descriptive_identity': ['P31', 'P279'],
    'dimension_length': ['P2043'],
    'mass': ['P2067'],
    'material_identity': ['P186'],
    'model_identifier': ['P2874']
}

subjects = []
with gzip.open('tasks/household/chunk-0024.csv.gz', 'rt') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        subjects.append({'key': row[0], 'name': row[1]})

name_to_keys = {}
for s in subjects:
    name_to_keys.setdefault(s['name'], []).append(s['key'])

results = []
cache_labels = {}

def cached_get_label(qid):
    if qid not in cache_labels:
        l = get_label(qid)
        cache_labels[qid] = l
    return cache_labels[qid]

print(f"Unique names: {len(name_to_keys)}")

for name, keys in list(name_to_keys.items()):
    title = search_wikipedia_title(name)
    if not title:
        qid = search_wikidata(name)
    else:
        qid = get_wikidata_id(title)

    if not qid:
        continue

    item = get_wikidata_item(qid)
    if not item:
        continue

    url = f"https://www.wikidata.org/wiki/{qid}"

    desc = item.get('descriptions', {}).get('en', {}).get('value')
    if desc:
        for key in keys:
            results.append([key, 'functional_summary', desc, url])

    label = item.get('labels', {}).get('en', {}).get('value')
    if label:
        for key in keys:
            results.append([key, 'identity_label', label, url])

    claims = item.get('claims', {})
    for col, props in PROP_MAP.items():
        for p in props:
            if p in claims:
                for claim in claims[p]:
                    if claim.get('mainsnak', {}).get('datavalue'):
                        val = resolve_claim(claim['mainsnak']['datavalue'])
                        if val is not None:
                            if claim['mainsnak']['datavalue']['type'] == 'wikibase-entityid':
                                val = cached_get_label(val)

                            # For outputting, strings shouldn't be dumped so they don't get double quotes,
                            # but wait, JSON strings shouldn't be parsed with csv writer.
                            # Just use raw strings.
                            if not isinstance(val, str):
                                val = json.dumps(float(val))

                            for key in keys:
                                results.append([key, col, val, url])

with open('out/household/chunk-0024.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
    writer.writerows(results)

print("Generated data.")
