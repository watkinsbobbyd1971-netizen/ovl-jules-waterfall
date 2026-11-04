import requests
import urllib.parse
import csv
import gzip
import time

def check_wikidata(query):
    # Try using wbsearchentities
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(query)}&language=en&format=json"
    headers = {"User-Agent": "MyBot/1.0"}
    try:
        response = requests.get(url, headers=headers).json()
        return response.get('search', [])
    except Exception as e:
        print(f"Error querying Wikidata: {e}")
        return []

print(check_wikidata("Pottery Wine-Cup"))
print(check_wikidata("Cupstone"))
print(check_wikidata("Ceramic"))
