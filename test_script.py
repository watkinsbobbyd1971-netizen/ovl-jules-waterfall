import urllib.request
import urllib.parse
import json
import gzip
import csv
import concurrent.futures
import time

def get_wikidata(subject_name):
    search_url = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=" + urllib.parse.quote(subject_name) + "&language=en&format=json"
    req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Bot)'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('search'):
                item_id = data['search'][0]['id']
                return item_id
    except Exception as e:
        print(f"Error searching {subject_name}: {e}")
    return None

def process_row(row):
    key = row['canonical_dedup_key']
    subject = row['subject_name']
    item_id = get_wikidata(subject)
    if not item_id:
        return []

    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={item_id}&format=json&props=claims|labels|descriptions"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Bot)'})
    results = []

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            entity = data['entities'][item_id]
            claims = entity.get('claims', {})
            source_url = f"https://www.wikidata.org/wiki/{item_id}"

            # Identity label
            labels = entity.get('labels', {})
            if 'en' in labels:
                results.append([key, 'identity_label', labels['en']['value'], source_url])

            # Descriptive identity
            descriptions = entity.get('descriptions', {})
            if 'en' in descriptions:
                results.append([key, 'descriptive_identity', descriptions['en']['value'], source_url])

            # Location (P131)
            if 'P131' in claims:
                for claim in claims['P131']:
                    val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                    if val:
                        # get label for val
                        loc_req = urllib.request.Request(f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={val}&format=json&props=labels", headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(loc_req) as loc_resp:
                            loc_data = json.loads(loc_resp.read().decode('utf-8'))
                            loc_label = loc_data['entities'][val].get('labels', {}).get('en', {}).get('value')
                            if loc_label:
                                results.append([key, 'location', loc_label, source_url])

            # Inception (P571) - construction_date
            if 'P571' in claims:
                for claim in claims['P571']:
                    val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('time')
                    if val:
                        # process time
                        if val.startswith('+'):
                            val = val[1:11] # YYYY-MM-DD
                        results.append([key, 'construction_date', val, source_url])

            # Coordinate location (P625) -> location? maybe skip

            # Architect (P84) -> creator_or_attribution
            if 'P84' in claims:
                for claim in claims['P84']:
                    val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                    if val:
                        arch_req = urllib.request.Request(f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={val}&format=json&props=labels", headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(arch_req) as arch_resp:
                            arch_data = json.loads(arch_resp.read().decode('utf-8'))
                            arch_label = arch_data['entities'][val].get('labels', {}).get('en', {}).get('value')
                            if arch_label:
                                results.append([key, 'creator_or_attribution', arch_label, source_url])
    except Exception as e:
        print(f"Error fetching details for {item_id}: {e}")
    time.sleep(0.5)
    return results

print(process_row({'canonical_dedup_key': 'LIBSRC-LIB58-ENT-BLD-0056709', 'subject_name': 'Lobras town hall'}))
