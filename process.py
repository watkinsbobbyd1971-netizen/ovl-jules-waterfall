import gzip
import csv
import json
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import os
import socket
import re
socket.setdefaulttimeout(10)

def search_ols(subject):
    query = urllib.parse.quote(subject)
    url = f"https://www.ebi.ac.uk/ols4/api/search?q={query}&ontology=uberon,fma&exact=true"
    req = urllib.request.Request(url, headers={'User-Agent': 'Script/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            docs = data.get('response', {}).get('docs', [])
            if docs:
                best_doc = docs[0]
                iri = best_doc.get('iri')
                label = best_doc.get('label')
                return iri, label, url
    except Exception as e:
        pass
    return None, None, None

def process_chunk():
    os.makedirs('out/human_anatomy', exist_ok=True)
    out_csv = 'out/human_anatomy/chunk-0018.csv'
    notes_txt = 'out/human_anatomy/chunk-0018.notes.txt'

    with open(notes_txt, 'w') as f:
        f.write("Used EBI OLS4 API (https://www.ebi.ac.uk/ols4/api/search) for ontology=uberon,fma\n")

    tasks = []
    with gzip.open('tasks/human_anatomy/chunk-0018.csv.gz', 'rt') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append((row['canonical_dedup_key'], row['subject_name']))

    cache = {}
    def process_task(task):
        key, subject = task
        # Basic clean subject name
        clean_subject = re.sub(r'\(.*?\)', '', subject).strip()
        clean_subject = re.sub(r'[",]', '', clean_subject)

        if clean_subject in cache:
            return key, cache[clean_subject]

        iri, label, url = search_ols(clean_subject)
        if not iri:
            # Try lowercasing
            iri, label, url = search_ols(clean_subject.lower())
        cache[clean_subject] = (iri, label, url)
        return key, (iri, label, url)

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for key, res in executor.map(process_task, tasks):
            results.append((key, res))

    with open(out_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])

        for key, (iri, label, url) in results:
            if iri and label:
                writer.writerow([key, 'anatomical_identity', json.dumps(iri), url])
                writer.writerow([key, 'identity_label', json.dumps(label), url])

if __name__ == '__main__':
    process_chunk()
