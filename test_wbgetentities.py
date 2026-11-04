import urllib.request
import urllib.parse
import json

def get_entities(ids):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbgetentities",
        "ids": "|".join(ids),
        "props": "claims",
        "format": "json"
    })
    req = urllib.request.Request(url, headers={"User-Agent": "MyBot/1.0 (https://example.org/mybot) bot@example.org"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

data = get_entities(["Q1570706", "Q82744"])
print(data["entities"]["Q1570706"]["claims"].keys())
