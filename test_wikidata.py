import urllib.request
import urllib.parse
import json

def search_wikidata(query):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "format": "json"
    })
    req = urllib.request.Request(url, headers={"User-Agent": "MyBot/1.0 (https://example.org/mybot) bot@example.org"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "search" in data and len(data["search"]) > 0:
                return data["search"][0]["id"]
    except Exception as e:
        print(f"Error for {query}: {e}")
    return None

print(search_wikidata("iconoscope"))
