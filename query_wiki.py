import urllib.request
import urllib.parse
import json

def get_wiki_info(title):
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exchars=500&titles={urllib.parse.quote(title)}&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'CoolBot/1.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        pages = data['query']['pages']
        for page_id, page_info in pages.items():
            if 'extract' in page_info:
                return page_info['extract']
    return None

print(get_wiki_info("Evelyn Nesbit"))
