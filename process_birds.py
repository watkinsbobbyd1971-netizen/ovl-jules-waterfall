import gzip
import csv
import json
import urllib.request
import urllib.parse
import re

def get_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        return json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
    except Exception as e:
        return None

def extract_name(subject_name):
    # Only try to extract from parens if it looks like a scientific name (two latin words)
    match = re.search(r'\(([A-Z][a-z]+ [a-z]+(?: [a-z]+)?)\)', subject_name)
    if match:
        return match.group(1)

    # If the whole thing looks like a scientific name
    match = re.match(r'^[A-Z][a-z]+ [a-z]+(?: [a-z]+)?$', subject_name)
    if match:
         return subject_name

    # Handle "Something (Adult)" -> "Something"
    match = re.match(r'([^(]+)\s*\(', subject_name)
    if match:
        return match.group(1).strip()

    return subject_name.strip()

def search_gbif(name):
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(name)}"
    resp = get_json(url)
    if resp and resp.get('matchType') == 'EXACT':
        # Ensure it's a bird
        if resp.get('class') == 'Aves':
            return resp
    return None

def process_file():
    input_file = "tasks/bird/chunk-0004.csv.gz"
    output_file = "out/bird/chunk-0004.csv"
    notes_file = "out/bird/chunk-0004.notes.txt"

    out_rows = []
    notes = ["Tried GBIF API (species/match) restricted to class Aves."]

    # Read all unique search terms
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

    for i, term in enumerate(term_list):
        if i % 50 == 0:
            print(f"Processed {i} terms")

        gbif_data = search_gbif(term)
        if gbif_data:
             source_url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(term)}"
             for key in terms_to_keys[term]:
                  if gbif_data.get('authorship'):
                       # Proper JSON encoding inside CSV means we format the string as `"""Value"""`
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
        # We must format it properly. Python's csv module handles quotes.
        # If we want literal """Value""", we just pass that string to writerow, and it will quote it if needed.
        # But wait, the memory says "JSON string 'Value' becomes '\"\"\"Value\"\"\"' in the raw CSV".
        # Let's just pass `"""Value"""` directly, and set quoting to QUOTE_NONE or let it quote.
        # If we pass `"""Value"""` and it quotes it, it becomes `""""""Value""""""`.
        # To avoid this and literally write `canonical_dedup_key,column_name,"""Value""",source_url`, we can write manually.
        f.write("canonical_dedup_key,column_name,value,source_url\n")
        for row in out_rows:
            f.write(f"{row['canonical_dedup_key']},{row['column_name']},{row['value']},{row['source_url']}\n")

    with open(notes_file, 'w') as f:
        f.write("\n".join(notes) + "\n")
    print(f"Finished. Total sourced values: {len(out_rows)}")

if __name__ == "__main__":
    process_file()
