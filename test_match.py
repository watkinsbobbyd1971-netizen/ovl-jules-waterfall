import urllib.request
import urllib.parse
import json
import re

terms = [
    "500 Unique Democratic Buttons",
    "Man's Hat",
    "Olivella callus bead, lipped",
    "Antler Arrohead, 1 Barb;",
    "Woman with Child",
    "ring setting",
    "3 Perforated Ivory Objects",
    "Ivory Carving Of Baby Seal",
    "Metal fragments"
]

for name in terms:
    last_word = name.split()[-1].lower().strip(";")
    url = f"https://www.ebi.ac.uk/ols4/api/search?q={urllib.parse.quote(last_word)}&exact=true&ontology=uberon,fma"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    docs = data.get('response', {}).get('docs', [])
    if docs:
        print(f"{name} -> {last_word} matched {docs[0]['label']} ({docs[0]['iri']})")
