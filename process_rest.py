import csv
import gzip
import json
import uuid
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import os

category = 'mineral_material'
chunk_id = '0021'
input_file = f'tasks/{category}/chunk-{chunk_id}.csv.gz'
output_file = f'out/{category}/chunk-{chunk_id}.csv'

chunk_keys = {}
with gzip.open(input_file, 'rt', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        chunk_keys[row['canonical_dedup_key']] = row['subject_name']

non_met_keys = {k: v for k, v in chunk_keys.items() if 'MET-' not in k}

def get_wikidata_item(label):
    # Try Wikipedia first
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(label)}&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            search_results = data.get('query', {}).get('search', [])
            if not search_results: return None

            title = search_results[0]['title']
            url2 = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&titles={urllib.parse.quote(title)}&format=json"
            req2 = urllib.request.Request(url2, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0'})
            with urllib.request.urlopen(req2, timeout=10) as response2:
                data2 = json.loads(response2.read().decode())
                pages = data2.get('query', {}).get('pages', {})
                for page_id, page_info in pages.items():
                    props = page_info.get('pageprops', {})
                    wb_item = props.get('wikibase_item')
                    if wb_item: return wb_item
    except Exception as e:
        pass
    return None

def process_item(item):
    k, v = item

    qid = get_wikidata_item(v)
    if not qid:
        parts = v.split()
        for word in parts:
            if word.lower() in ['stibnite', 'fudo', 'missal', 'caboclo', 'eugenics']:
                qid = get_wikidata_item(word)
                if qid:
                    break

    results = []
    if qid:
        url3 = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={qid}&props=claims&format=json"
        req3 = urllib.request.Request(url3, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0'})
        try:
            with urllib.request.urlopen(req3, timeout=10) as response3:
                data3 = json.loads(response3.read().decode())
                claims = data3.get('entities', {}).get(qid, {}).get('claims', {})
                # Material P186
                if 'P186' in claims:
                    for claim in claims['P186']:
                        m_id = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                        if m_id:
                            # Get material label
                            url4 = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={m_id}&props=labels&format=json"
                            req4 = urllib.request.Request(url4, headers={'User-Agent': f'MyBot_{uuid.uuid4().hex[:8]}/1.0'})
                            with urllib.request.urlopen(req4, timeout=10) as response4:
                                data4 = json.loads(response4.read().decode())
                                label = data4.get('entities', {}).get(m_id, {}).get('labels', {}).get('en', {}).get('value')
                                if label:
                                    results.append({
                                        'canonical_dedup_key': k,
                                        'column_name': 'material_identity',
                                        'value': json.dumps(label),
                                        'source_url': f"https://www.wikidata.org/wiki/{qid}"
                                    })
        except Exception as e:
            pass
    return results

out_rows = []
with ThreadPoolExecutor(max_workers=5) as executor:
    for results in executor.map(process_item, non_met_keys.items()):
        out_rows.extend(results)

print(f"Found {len(out_rows)} non-MET rows.")

with open(output_file, 'a', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
    for row in out_rows:
        writer.writerow(row)
