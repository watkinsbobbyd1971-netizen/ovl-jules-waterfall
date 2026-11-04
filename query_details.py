import urllib.request
import json
url = "https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q126816734&format=json"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        print(json.dumps(json.loads(response.read().decode('utf-8')), indent=2))
except Exception as e:
    print(e)
