import urllib.request
import urllib.parse
import json
import gzip
import csv
import concurrent.futures

def check_ols(term):
    url = f"https://www.ebi.ac.uk/ols4/api/search?q={urllib.parse.quote(term)}&ontology=fma,uberon&exact=true"
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('response', {}).get('numFound', 0) > 0:
                for doc in data['response']['docs']:
                    label = doc.get("label", "")
                    ontology_name = doc.get("ontology_name", "").lower()
                    obo_id = doc.get("obo_id", "").upper()

                    if label.lower() == term.lower() and ontology_name in ["fma", "uberon"]:
                        if obo_id.startswith("UBERON:") or obo_id.startswith("FMA:"):
                            return doc
    except:
        pass

    url = f"https://www.ebi.ac.uk/ols4/api/search?q={urllib.parse.quote(term)}&ontology=fma,uberon"
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('response', {}).get('numFound', 0) > 0:
                for doc in data['response']['docs']:
                    label = doc.get("label", "")
                    ontology_name = doc.get("ontology_name", "").lower()
                    obo_id = doc.get("obo_id", "").upper()

                    if label.lower() == term.lower() and ontology_name in ["fma", "uberon"]:
                        if obo_id.startswith("UBERON:") or obo_id.startswith("FMA:"):
                            return doc
    except:
        pass

    return None

def process_subject(row):
    subject = row['subject_name']

    # We should also query to see if there are matches in wikidata but since we already queried OLS exactly for anatomy,
    # maybe this chunk doesn't have many anatomy properties. Let's see if we can extract from Wikipedia or Wikidata.

    # Actually wait. Let's look closely at the subjects: they are museum artifacts like prints, drawings, sculptures.
    # The chunk is filled with things like "Portrait of Deloris Porter", "postcard", "Cornice (Ceiling) Design".
    # These are not human anatomical structures.
    # Let's verify by just printing out random subjects from this chunk.
    return None

if __name__ == "__main__":
    import gzip, csv
    with gzip.open('tasks/human_anatomy/chunk-0013.csv.gz', 'rt', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        for i in range(0, 1000, 100):
            print(reader[i]['subject_name'])
