import urllib.request
import urllib.parse
import json
import gzip
import csv

def get_wikidata_entity(query):
    # Wikidata title search
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CoolBot/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('query', {}).get('search'):
                title = data['query']['search'][0]['title']
                return title
    except:
        pass
    return None

with gzip.open('tasks/cultural_object/chunk-0002.csv.gz', 'rt') as f:
    reader = csv.reader(f)
    next(reader)
    count = 0
    for row in reader:
        title = get_wikidata_entity(row[1])
        if title:
            print(f"{row[0]} - {row[1]} -> Wiki: {title}")
            count += 1
        if count >= 15:
            break
