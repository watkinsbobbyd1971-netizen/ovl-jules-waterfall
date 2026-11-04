import urllib.request
import json

def get_property_label(prop_id):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={prop_id}&props=labels&languages=en&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data['entities'][prop_id]['labels']['en']['value']
    except Exception as e:
        return prop_id

props = ['P176', 'P170', 'P571', 'P31', 'P2043', 'P2067', 'P186', 'P366']
for p in props:
    print(f"{p}: {get_property_label(p)}")
