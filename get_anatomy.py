import csv
import gzip
import json
import os
import re
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import time

INPUT_FILE = 'tasks/human_anatomy/chunk-0012.csv.gz'
OUTPUT_DIR = 'out/human_anatomy'
OUTPUT_FILE = f'{OUTPUT_DIR}/chunk-0012.csv'
NOTES_FILE = f'{OUTPUT_DIR}/chunk-0012.notes.txt'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Columns allowed: anatomical_identity, anatomical_length, anatomical_relationship, descriptive_identity, identity_label, morphology, tissue_identity

def search_ols_for_term(term):
    if not term:
        return None, None
    term_quote = urllib.parse.quote(term)
    url = f"https://www.ebi.ac.uk/ols4/api/search?q={term_quote}&exact=true&ontology=uberon,fma"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        docs = data.get('response', {}).get('docs', [])
        for doc in docs:
            label = doc.get('label', '').lower()
            if label == term.lower():
                return doc.get('iri'), url
            synonyms = [syn.lower() for syn in doc.get('exact_synonyms', [])]
            if term.lower() in synonyms:
                return doc.get('iri'), url
    except Exception as e:
        pass
    return None, None

def extract_anatomical_term(subject_name):
    # These artifacts have some anatomy names in them
    s = subject_name.lower()
    s = re.sub(r'\(image withheld\)', '', s).strip()
    words = re.findall(r'[a-z]+', s)

    # Try some specific anatomical terms if they exist as separate words
    known_terms = ["bone", "mandible", "vertebra", "femur", "scapula", "skull", "tooth", "skeleton", "shell", "scale", "rib", "pelvis", "clavicle", "humerus", "radius", "ulna", "tibia", "fibula", "patella", "carpal", "metacarpal", "phalange", "tarsal", "metatarsal"]

    for term in known_terms:
        if term in words:
            return term

    # Use the last whole word if we don't have a known match
    if words:
        return words[-1]

    return None

def process_subject(item):
    key, subject_name = item
    time.sleep(0.01)  # tiny sleep to prevent massive burst

    # Try the full string first
    iri, url = search_ols_for_term(subject_name)
    if iri:
        return (key, subject_name, iri, url)

    # Try exact match first for extracted terms
    term = extract_anatomical_term(subject_name)
    if term:
        iri, url = search_ols_for_term(term)
        if iri:
            return (key, term, iri, url)

    return None

def main():
    with gzip.open(INPUT_FILE, 'rt') as f:
        reader = csv.reader(f)
        next(reader)
        subjects = [(row[0], row[1]) for row in reader]

    print(f"Loaded {len(subjects)} subjects. Processing...")

    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        for i, res in enumerate(executor.map(process_subject, subjects)):
            if res:
                results.append(res)
            if (i+1) % 100 == 0:
                print(f"Processed {i+1}/{len(subjects)}")

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])

        for key, term, iri, url in results:
            writer.writerow([key, 'anatomical_identity', json.dumps(iri), url])
            writer.writerow([key, 'identity_label', json.dumps(term), url])

    with open(NOTES_FILE, 'w') as f:
        f.write("Queried EBI OLS API (UBERON and FMA ontologies) for anatomical terms.\n")

    print(f"Done. Found {len(results)} matches.")

if __name__ == '__main__':
    main()
