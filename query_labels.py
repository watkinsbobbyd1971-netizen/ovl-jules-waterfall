import urllib.request
import json
import time

def get_label(entity_id):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&props=labels&languages=en&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data['entities'][entity_id]['labels']['en']['value']
    except Exception as e:
        print(f"Error for {entity_id}: {e}")
        return entity_id

print(get_label("Q1469447"))
print(get_label("Q15142894"))
