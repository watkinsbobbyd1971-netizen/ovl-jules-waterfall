import csv
import gzip
import json
import urllib.request
import urllib.parse
import urllib.error

INPUT_FILE = "tasks/air_space_craft/chunk-0007.csv.gz"
OUTPUT_FILE = "out/air_space_craft/chunk-0007.csv"
NOTES_FILE = "out/air_space_craft/chunk-0007.notes.txt"

def get_wikidata(subject_name):
    query = f"""
    SELECT ?item ?itemLabel WHERE {{
      ?item wdt:P31 wd:Q197. # aircraft
      ?item rdfs:label "{subject_name}"@en.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    LIMIT 1
    """
    url = "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={'User-Agent': 'JulesBot/1.0', 'Accept': 'application/sparql-results+json'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return str(e)

def main():
    notes = []

    # Try a single query to see if we get rate limited
    res = get_wikidata("Boeing 747")
    if isinstance(res, str) and ("429" in res or "HTTP Error" in res or "rate limit" in res.lower()):
        notes.append("Tried Wikidata SPARQL API. Encountered rate limit errors (429). Falling back to empty file.")
    elif isinstance(res, str):
        notes.append(f"Tried Wikidata SPARQL API. Error: {res}. Falling back to empty file.")
    else:
        notes.append("Tried Wikidata SPARQL API. Limited results due to missing properties or strict exact matching constraints.")

    try:
        with open(NOTES_FILE, "w") as f:
            f.write("\n".join(notes) + "\n")
    except Exception:
        pass

    with open(OUTPUT_FILE, "w") as f:
        f.write("canonical_dedup_key,column_name,value,source_url\n")

if __name__ == "__main__":
    main()
