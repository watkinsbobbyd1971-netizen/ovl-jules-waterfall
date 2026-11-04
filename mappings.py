import requests

def get_entity_data(entity_id):
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&languages=en&format=json"
    headers = {"User-Agent": "JulesCulturalBot/1.0 (test@test.com)"}
    try:
        response = requests.get(url, headers=headers).json()
        return response.get('entities', {}).get(entity_id, {})
    except Exception as e:
        print(e)
        return {}

def print_values(entity_id, prop):
    data = get_entity_data(entity_id)
    claims = data.get('claims', {}).get(prop, [])
    for claim in claims:
        print(claim['mainsnak']['datavalue'])

print_values("Q15711817", "P279") # subclass of
