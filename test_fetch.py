import urllib.request
print("starting")
req = urllib.request.Request("https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Lobras+town+hall&language=en&format=json", headers={'User-Agent': 'Mozilla/5.0 (Bot)'})
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode('utf-8')[:100])
except Exception as e:
    print(e)
print("done")
