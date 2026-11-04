import gzip
import csv
import urllib.request
import urllib.parse
import json

def get_wikidata_entity(subject):
    query = f"SELECT ?item ?itemLabel WHERE {{ ?item wdt:P31/wdt:P279* wd:Q202866. ?item rdfs:label ?itemLabel. FILTER(LANG(?itemLabel) = 'en') FILTER(LCASE(?itemLabel) = LCASE('{subject}')) }} LIMIT 1"
    url = "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0', 'Accept': 'application/sparql-results+json'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            bindings = data.get('results', {}).get('bindings', [])
            if bindings:
                return bindings[0]['item']['value']
    except Exception as e:
        print(f"Error querying {subject}: {e}")
    return None

def main():
    with gzip.open('tasks/human_anatomy/chunk-0013.csv.gz', 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i > 10:
                break
            subject = row['subject_name']
            entity = get_wikidata_entity(subject)
            print(f"{subject}: {entity}")

if __name__ == "__main__":
    main()
