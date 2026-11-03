import urllib.request
import urllib.parse
import json
import re

def search_pmc(query):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={urllib.parse.quote(query)}&retmode=json&retmax=5"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    return data['esearchresult']['idlist']

q = '("Sumatran rhinoceros" OR "Dicerorhinus sumatrensis") AND (mass OR weight) AND length AND ("2020/01/01"[PubDate] : "2026/12/31"[PubDate])'
print(search_pmc(q))
