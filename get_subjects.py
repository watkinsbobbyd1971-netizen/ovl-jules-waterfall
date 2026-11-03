import urllib.request
import json
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def search(query):
    url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        res = urllib.request.urlopen(req, context=ctx).read()
        return json.loads(res)['query']['search']
    except Exception as e:
        return []

def get_text(title):
    url = f'https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&titles={urllib.parse.quote(title)}&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        res = urllib.request.urlopen(req, context=ctx).read()
        data = json.loads(res)
        pages = data['query']['pages']
        for p in pages:
            return pages[p]['revisions'][0]['*']
    except Exception as e:
        return ""

print("Searching meteorites...")
results = search("meteorite 2020 OR meteorite 2021 OR meteorite 2022")
for r in results:
    print(r['title'])
