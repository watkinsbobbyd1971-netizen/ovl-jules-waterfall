import csv
import gzip
import json
import urllib.request
import urllib.parse

def search_wikidata(query):
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(query)}&language=en&format=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('search'):
                return data['search'][0]['id']
    except Exception as e:
        print(f"Error searching {query}: {e}")
    return None

with gzip.open('tasks/cultural_object/chunk-0002.csv.gz', 'rt') as f:
    reader = csv.reader(f)
    next(reader)
    for row in list(reader)[:10]:
        print(row[1], search_wikidata(row[1]))
