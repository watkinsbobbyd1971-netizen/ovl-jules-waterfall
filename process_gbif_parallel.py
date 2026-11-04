import gzip
import csv
import json
import urllib.request
import urllib.parse
import re
import concurrent.futures

def get_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        return json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
    except Exception as e:
        return None

def extract_name(subject_name):
    match = re.search(r'\(([A-Z][a-z]+ [a-z]+(?: [a-z]+)?)\)', subject_name)
    if match:
        return match.group(1)
    match = re.match(r'^[A-Z][a-z]+ [a-z]+(?: [a-z]+)?$', subject_name)
    if match:
         return subject_name
    match = re.match(r'([^(]+)\s*\(', subject_name)
    if match:
        return match.group(1).strip()
    return subject_name.strip()

def process_term(term):
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(term)}"
    resp = get_json(url)
    if resp and resp.get('matchType') == 'EXACT' and resp.get('class') == 'Aves':
        return term, resp, url
    return term, None, url

def process_file():
    input_file = "tasks/bird/chunk-0004.csv.gz"
    output_file = "out/bird/chunk-0004.csv"
    notes_file = "out/bird/chunk-0004.notes.txt"

    out_rows = []
    notes = ["Tried GBIF API (species/match) restricted to class Aves. Parallelized for speed."]

    terms_to_keys = {}
    with gzip.open(input_file, 'rt') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row['canonical_dedup_key']
            subj = row['subject_name']

            search_term = extract_name(subj)
            if search_term not in terms_to_keys:
                terms_to_keys[search_term] = []
            terms_to_keys[search_term].append(key)

    term_list = list(terms_to_keys.keys())
    print(f"Total unique terms: {len(term_list)}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(process_term, term_list))

    for term, gbif_data, source_url in results:
        if gbif_data:
             for key in terms_to_keys[term]:
                  if gbif_data.get('authorship'):
                       val_str = f'"""{gbif_data["authorship"]}"""'
                       out_rows.append({
                            'canonical_dedup_key': key,
                            'column_name': 'taxon_authority',
                            'value': val_str,
                            'source_url': source_url
                       })
                  if gbif_data.get('scientificName'):
                       canon = gbif_data.get('canonicalName', gbif_data['scientificName'])
                       val_str = f'"""{canon}"""'
                       out_rows.append({
                            'canonical_dedup_key': key,
                            'column_name': 'scientific_identity',
                            'value': val_str,
                            'source_url': source_url
                       })

    with open(output_file, 'w', newline='') as f:
        f.write("canonical_dedup_key,column_name,value,source_url\n")
        for row in out_rows:
            f.write(f"{row['canonical_dedup_key']},{row['column_name']},{row['value']},{row['source_url']}\n")

    with open(notes_file, 'w') as f:
        f.write("\n".join(notes) + "\n")
    print(f"Finished. Total sourced values: {len(out_rows)}")

if __name__ == "__main__":
    process_file()
