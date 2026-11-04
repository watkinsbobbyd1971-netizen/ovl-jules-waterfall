import urllib.request
import urllib.parse
import json

def get_wikidata_claims(title):
    # get Wikidata Q-ID from Wikipedia title
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&titles={urllib.parse.quote(title)}&format=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CoolBot/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_info in pages.items():
                if 'pageprops' in page_info and 'wikibase_item' in page_info['pageprops']:
                    qid = page_info['pageprops']['wikibase_item']
                    return qid
    except Exception as e:
        print(e)
    return None

print(get_wikidata_claims("Evelyn Nesbit"))
