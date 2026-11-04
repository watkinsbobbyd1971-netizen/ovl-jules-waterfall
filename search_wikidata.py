import requests
import urllib.parse

def search_wikidata(query):
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(query)}&language=en&format=json"
    headers = {"User-Agent": "MyBot/1.0"}
    response = requests.get(url, headers=headers).json()
    return response.get('search', [])

print(search_wikidata("0817784"))
print(search_wikidata("LIBSRC-LIB51-ENT-SMI-0817784"))
print(search_wikidata("Broken Ceramic Jar"))
