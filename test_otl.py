import urllib.request
import urllib.parse
import json

url = "https://api.opentreeoflife.org/v3/tnrs/match_names"
data = json.dumps({"names": ["Megaceryle alcyon", "Gavia immer"]}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    resp = urllib.request.urlopen(req)
    res = json.loads(resp.read())
    print(json.dumps(res, indent=2))
except Exception as e:
    print(e)
