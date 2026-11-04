import urllib.request
import urllib.parse
import json
import gzip
import csv

def get_smithsonian_data(query):
    # Smithsonian api key is needed but we can also use public search
    pass

def get_met_data(query):
    url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('objectIDs'):
                return data['objectIDs'][0]
    except:
        pass
    return None

with gzip.open('tasks/cultural_object/chunk-0002.csv.gz', 'rt') as f:
    reader = csv.reader(f)
    next(reader)
    for row in list(reader)[:10]:
        print(row[1], "Met:", get_met_data(row[1]))
