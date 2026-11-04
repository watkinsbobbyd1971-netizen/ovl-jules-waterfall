import requests

def get_label(entity_id):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&props=labels&languages=en&format=json"
    headers = {"User-Agent": "JulesCulturalBot/1.0 (test@test.com)"}
    try:
        response = requests.get(url, headers=headers).json()
        return response.get('entities', {}).get(entity_id, {}).get('labels', {}).get('en', {}).get('value', '')
    except Exception as e:
        print(e)
        return ''

print(get_label("P2079"))
