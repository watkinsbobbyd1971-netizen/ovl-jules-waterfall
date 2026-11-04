import urllib.request
import urllib.parse
import json
import gzip
import csv

def get_smithsonian(query):
    url = f"https://api.si.edu/openaccess/api/v1.0/search?q={urllib.parse.quote(query)}"
    try:
        # without api key this might fail
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('response', {}).get('rows'):
                return data['response']['rows'][0]['id']
    except Exception as e:
        # print(e)
        pass
    return None

with gzip.open('tasks/cultural_object/chunk-0002.csv.gz', 'rt') as f:
    reader = csv.reader(f)
    next(reader)
    for row in list(reader)[:10]:
        print(row[1], "SI:", get_smithsonian(row[1]))
