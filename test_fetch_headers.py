import urllib.request
import time
print("starting")
req = urllib.request.Request("https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Lobras+town+hall&language=en&format=json", headers={
    'User-Agent': 'CoolBot/1.0 (someone@example.com)'
})
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode('utf-8')[:100])
except Exception as e:
    print(e)
print("done")
