import urllib.request
import urllib.parse
import json
import gzip
import csv
import sys

def search_edan(query):
    # Smithsonian EDAN allows some public query? No, we don't have API keys.
    # Let's try to query the Smithsonian collections page
    url = f"https://collections.si.edu/search/results.htm?q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode()
            if "No results found" not in html:
                return True
    except:
        pass
    return False

with gzip.open('tasks/cultural_object/chunk-0002.csv.gz', 'rt') as f:
    reader = csv.reader(f)
    next(reader)
    for row in list(reader)[:10]:
        print(row[1], search_edan(row[0]))
