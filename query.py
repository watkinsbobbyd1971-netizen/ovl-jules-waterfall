import urllib.request
import urllib.parse
import json
import gzip
import csv

sparql_query = """
SELECT ?item ?itemLabel ?coord ?inception ?architect ?architectLabel ?location ?locationLabel WHERE {
  ?item wdt:P31/wdt:P279* wd:Q25550691 ; # town hall in Spain? wait, town hall is Q105470
       wdt:P17 wd:Q29 .
  OPTIONAL { ?item wdt:P625 ?coord . }
  OPTIONAL { ?item wdt:P571 ?inception . }
  OPTIONAL { ?item wdt:P84 ?architect . }
  OPTIONAL { ?item wdt:P131 ?location . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} LIMIT 100
"""

# Let's search by string first using wbsearchentities
search_url = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=" + urllib.parse.quote("Lobras town hall") + "&language=en&format=json"
req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode('utf-8'))
except Exception as e:
    print(e)
