import urllib.request
import urllib.parse
import json
import gzip
import csv
import os
import time

def query_wikidata(subject_name):
    # First search for the entity
    search_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(subject_name)}&language=en&format=json"
    req = urllib.request.Request(search_url, headers={'User-Agent': 'MyBot/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            search_data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error searching for {subject_name}: {e}")
        return []

    if not search_data.get('search'):
        return []

    results = []
    # If the exact name matches
    for item in search_data['search']:
        if item.get('match', {}).get('text', '').lower() == subject_name.lower():
            entity_id = item['id']
            # Fetch entity properties
            entity_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json"
            req2 = urllib.request.Request(entity_url, headers={'User-Agent': 'MyBot/1.0'})
            try:
                with urllib.request.urlopen(req2) as response:
                    entity_data = json.loads(response.read().decode())
            except Exception as e:
                print(f"Error fetching entity {entity_id}: {e}")
                continue

            if 'entities' in entity_data and entity_id in entity_data['entities']:
                claims = entity_data['entities'][entity_id].get('claims', {})

                # Check for creator/manufacturer (P176 - manufacturer, P170 - creator)
                for prop_id in ['P176', 'P170']:
                    if prop_id in claims:
                        for claim in claims[prop_id]:
                            if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'wikibase-entityid':
                                creator_id = claim['mainsnak']['datavalue']['value']['id']
                                # Could resolve this ID but returning the ID string for now to see if it works
                                results.append({
                                    'column_name': 'creator_or_attribution',
                                    'value': f'"{creator_id}"', # Should be JSON encoded
                                    'source_url': f"https://www.wikidata.org/wiki/{entity_id}"
                                })

                # P2067 - mass (g)
                if 'P2067' in claims:
                    for claim in claims['P2067']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'quantity':
                            amount = claim['mainsnak']['datavalue']['value']['amount']
                            unit = claim['mainsnak']['datavalue']['value']['unit']
                            amount = float(amount.strip('+'))

                            # Convert to grams if possible
                            if 'Q41803' in unit: # gram
                                val = amount
                            elif 'Q11570' in unit: # kilogram
                                val = amount * 1000
                            else:
                                val = amount # Default, might be wrong

                            results.append({
                                'column_name': 'mass',
                                'value': str(val),
                                'source_url': f"https://www.wikidata.org/wiki/{entity_id}"
                            })

                # P2043 - length (mm)
                if 'P2043' in claims:
                    for claim in claims['P2043']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'quantity':
                            amount = claim['mainsnak']['datavalue']['value']['amount']
                            unit = claim['mainsnak']['datavalue']['value']['unit']
                            amount = float(amount.strip('+'))

                            if 'Q174789' in unit: # millimeter
                                val = amount
                            elif 'Q174728' in unit: # centimeter
                                val = amount * 10
                            elif 'Q11573' in unit: # meter
                                val = amount * 1000
                            else:
                                val = amount

                            results.append({
                                'column_name': 'dimension_length',
                                'value': str(val),
                                'source_url': f"https://www.wikidata.org/wiki/{entity_id}"
                            })

                # P31 - instance of (descriptive_identity)
                if 'P31' in claims:
                    for claim in claims['P31']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'wikibase-entityid':
                            val_id = claim['mainsnak']['datavalue']['value']['id']
                            results.append({
                                'column_name': 'descriptive_identity',
                                'value': f'"{val_id}"', # Will be resolved later
                                'source_url': f"https://www.wikidata.org/wiki/{entity_id}"
                            })

                # P571 - inception (date_or_interval)
                if 'P571' in claims:
                    for claim in claims['P571']:
                        if claim.get('mainsnak', {}).get('datavalue', {}).get('type') == 'time':
                            time_val = claim['mainsnak']['datavalue']['value']['time']
                            results.append({
                                'column_name': 'date_or_interval',
                                'value': f'"{time_val}"',
                                'source_url': f"https://www.wikidata.org/wiki/{entity_id}"
                            })

            break # Only take the first exact match

    time.sleep(0.1) # Rate limit
    return results

print(query_wikidata("Winchester Model 1873"))
