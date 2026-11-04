import requests
import urllib.parse
import json

def search_wikidata_inventory(inv_num):
    # Try different combinations of the ID
    query = f"""
    SELECT ?item ?itemLabel ?inv WHERE {{
      ?item wdt:P217 ?inv .
      FILTER(CONTAINS(STR(?inv), "{inv_num}"))
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    """
    url = "https://query.wikidata.org/sparql"
    headers = {"User-Agent": "MyBot/1.0", "Accept": "application/sparql-results+json"}
    response = requests.get(url, params={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json().get('results', {}).get('bindings', [])
    else:
        return response.text

print(search_wikidata_inventory("SMI-0817784"))
print(search_wikidata_inventory("0817784"))
