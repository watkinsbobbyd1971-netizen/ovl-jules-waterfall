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

    # Check if we should skip typical museum artifact names that coincidentally match
    skip_terms = {"rattle", "bar", "drawing", "print", "figure", "blank", "slip", "nodule", "blade", "blanket", "border", "ribbon", "tracing", "whip", "compact"}
    if subject.strip().lower() in skip_terms:
        return None

    clean_subject = subject.strip()
    doc = check_ols(clean_subject)
    if not doc:
        doc = check_ols(clean_subject.lower())

    if doc:
        return {
            'canonical_dedup_key': row['canonical_dedup_key'],
            'subject': subject,
            'anatomical_identity': doc.get("label", ""),
            'source_url': doc.get('iri', f"https://www.ebi.ac.uk/ols4/search?q={urllib.parse.quote(subject)}")
        }
    return None

def main():
    results = []

    with gzip.open('tasks/human_anatomy/chunk-0013.csv.gz', 'rt', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for res in executor.map(process_subject, reader):
            if res:
                results.append(res)

    with open('out/human_anatomy/chunk-0013.csv', 'w', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        for r in results:
            json_val = json.dumps(r['anatomical_identity'])
            writer.writerow([r['canonical_dedup_key'], 'anatomical_identity', json_val, r['source_url']])

    with open('out/human_anatomy/chunk-0013.notes.txt', 'w') as f:
        f.write("Queried OLS (fma,uberon) for exact matches of subject names, filtering out non-FMA/UBERON prefixes and obvious museum false positives.\n")

if __name__ == "__main__":
    main()
