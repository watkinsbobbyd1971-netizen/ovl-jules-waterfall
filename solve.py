import gzip
import csv
import json
import urllib.request
import urllib.parse
import time
import os
import ssl

from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cache_search = {}
cache_get = {}

def search_wikidata(name):
    if name in cache_search:
        return cache_search[name]

    clean_name = name
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            clean_name = parts[1].strip() + ' ' + parts[0].strip()

    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbsearchentities",
        "search": clean_name,
        "language": "en",
        "format": "json",
        "limit": 1
    })
    req = urllib.request.Request(url, headers={"User-Agent": "MyBot/1.0 (jules@example.com)"})
    for _ in range(2):
        try:
            with urllib.request.urlopen(req, context=ctx) as resp:
                res = json.loads(resp.read().decode())
                if res.get('search'):
                    val = res['search'][0]['id']
                    cache_search[name] = val
                    return val

                # fallback to original name
                if clean_name != name:
                    url2 = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
                        "action": "wbsearchentities",
                        "search": name,
                        "language": "en",
                        "format": "json",
                        "limit": 1
                    })
                    req2 = urllib.request.Request(url2, headers={"User-Agent": "MyBot/1.0 (jules@example.com)"})
                    with urllib.request.urlopen(req2, context=ctx) as resp2:
                        res2 = json.loads(resp2.read().decode())
                        if res2.get('search'):
                            val = res2['search'][0]['id']
                            cache_search[name] = val
                            return val
                cache_search[name] = None
                return None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2)
            else:
                return None
        except Exception:
            pass
    return None

def get_wikidata_entity(qid):
    if qid in cache_get:
        return cache_get[qid]

    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbgetentities",
        "ids": qid,
        "props": "claims|labels",
        "languages": "en",
        "format": "json"
    })
    req = urllib.request.Request(url, headers={"User-Agent": "MyBot/1.0 (jules@example.com)"})
    for _ in range(2):
        try:
            with urllib.request.urlopen(req, context=ctx) as resp:
                data = json.loads(resp.read().decode())
                cache_get[qid] = data
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2)
            else:
                return None
        except Exception:
            pass
    return None

def process_row(row):
    key, name = row
    qid = search_wikidata(name)
    if not qid:
        return []

    entity_data = get_wikidata_entity(qid)
    if not entity_data or 'entities' not in entity_data or qid not in entity_data['entities']:
        return []

    entity = entity_data['entities'][qid]
    claims = entity.get('claims', {})

    results = []
    source_url = f"https://www.wikidata.org/wiki/{qid}"

    props_map = {
        "P527": "component_relationship",
        "P31": "descriptive_identity",
        "P279": "descriptive_identity",
        "P2043": "dimension_length",
        "P176": "manufacturer_or_creator",
        "P170": "manufacturer_or_creator",
        "P2067": "mass",
        "P186": "material_identity",
        "P2050": "span"
    }

    for p_id, col_name in props_map.items():
        if p_id in claims:
            for c in claims[p_id]:
                try:
                    if c.get('mainsnak', {}).get('snaktype') == 'value':
                        val = c['mainsnak']['datavalue']['value']
                        if p_id in ['P2043', 'P2067', 'P2050']:
                            amount_str = val['amount']
                            if amount_str.startswith('+'):
                                amount_str = amount_str[1:]
                            amount = float(amount_str)
                            unit = val['unit']
                            if p_id in ['P2043', 'P2050']: # mm
                                if unit == 'http://www.wikidata.org/entity/Q11573': # metre
                                    amount *= 1000
                                elif unit == 'http://www.wikidata.org/entity/Q174789': # mm
                                    pass
                                elif unit == 'http://www.wikidata.org/entity/Q174728': # cm
                                    amount *= 10
                                else:
                                    continue
                                results.append([key, col_name, str(amount), source_url])
                            elif p_id == 'P2067': # g
                                if unit == 'http://www.wikidata.org/entity/Q11570': # kg
                                    amount *= 1000
                                elif unit == 'http://www.wikidata.org/entity/Q41803': # g
                                    pass
                                elif unit == 'http://www.wikidata.org/entity/Q100995': # pound
                                    amount *= 453.592
                                else:
                                    continue
                                results.append([key, col_name, str(amount), source_url])
                        else:
                            if isinstance(val, dict) and 'id' in val:
                                target_qid = val['id']
                                label_data = get_wikidata_entity(target_qid)
                                if label_data and 'entities' in label_data and target_qid in label_data['entities']:
                                    labels = label_data['entities'][target_qid].get('labels', {})
                                    if 'en' in labels:
                                        label = labels['en']['value']
                                        json_val = json.dumps(label)
                                        results.append([key, col_name, json_val, source_url])
                except Exception as e:
                    pass

    if 'labels' in entity and 'en' in entity['labels']:
        json_val = json.dumps(entity['labels']['en']['value'])
        results.append([key, "identity_label", json_val, source_url])

    return results

def main():
    os.makedirs("out/air_space_craft", exist_ok=True)
    out_path = "out/air_space_craft/chunk-0014.csv"

    with gzip.open("tasks/air_space_craft/chunk-0014.csv.gz", "rt") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    all_results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        for res in executor.map(process_row, rows):
            all_results.extend(res)

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["canonical_dedup_key", "column_name", "value", "source_url"])
        writer.writerows(all_results)

    with open("out/air_space_craft/chunk-0014.notes.txt", "w") as f:
        f.write("Queried Wikidata for all subjects. Extracted properties mapped to allowed columns: P527, P31, P279, P2043, P176, P170, P2067, P186, P2050, and labels.\n")

if __name__ == "__main__":
    main()
