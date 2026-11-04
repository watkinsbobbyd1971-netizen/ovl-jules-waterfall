import urllib.request
import urllib.parse
import json

def get_rijks(query):
    url = f"https://www.rijksmuseum.nl/api/en/collection?key=0fiuZFhW&q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('artObjects'):
                for obj in data['artObjects']:
                    print(obj['title'], obj['objectNumber'])
                    return obj
    except:
        pass
    return None

get_rijks("Evelyn Nesbit")
