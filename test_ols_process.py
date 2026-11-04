import urllib.request
import urllib.parse
import json
import re
import csv
import gzip

def normalize_subject(subject_name):
    # This dataset seems to contain mixed objects, some of which have biological parts.
    # The user says: "For human anatomy corpus tasks, the EBI OLS (Ontology Lookup Service) API is an effective public structured source for querying FMA and UBERON ontologies to find exact matches."
    # Let's extract words that might be anatomy
    s = subject_name.lower().strip()
    s = re.sub(r'\(image withheld\)', '', s).strip()
    s = re.sub(r'[^a-z ]', '', s)
    words = s.split()
    # Check if any word is an exact match for common anatomy terms, or try all words.
    return s

def search_ols(term):
    if not term:
        return None, None, None
    term_quote = urllib.parse.quote(term)
    url = f"https://www.ebi.ac.uk/ols4/api/search?q={term_quote}&exact=true&ontology=uberon,fma"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        docs = data.get('response', {}).get('docs', [])
        # Only accept exact matches for the label
        for doc in docs:
            label = doc.get('label', '').lower()
            if label == term.lower():
                return doc.get('iri'), doc.get('label'), url
            synonyms = [syn.lower() for syn in doc.get('exact_synonyms', [])]
            if term.lower() in synonyms:
                return doc.get('iri'), doc.get('label'), url
    except Exception as e:
        pass
    return None, None, None

with gzip.open('tasks/human_anatomy/chunk-0012.csv.gz', 'rt') as f:
    reader = csv.reader(f)
    next(reader)
    subjects = [(row[0], row[1]) for row in reader]

matched_count = 0
for key, name in subjects[:500]:
    s = re.sub(r'[^a-zA-Z \-]', '', name).strip()
    words = s.split()

    # Check the whole string first
    iri, label, url = search_ols(name.lower())

    # Check specific words from the end if the whole string didn't match
    if not iri and len(words) > 0:
        for i in range(min(5, len(words))):
            word = words[-1 - i].lower()
            iri, label, url = search_ols(word)
            if iri:
                break

    if iri:
        print(f"Match: {name} -> {label} ({iri})")
        matched_count += 1

print(f"Total matched: {matched_count}/500")
