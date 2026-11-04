import urllib.request
import urllib.parse
import json
import gzip
import csv
import concurrent.futures

def check_ols(subject):
    url = f"https://www.ebi.ac.uk/ols4/api/search?q={urllib.parse.quote(subject)}&ontology=fma,uberon&exact=true"
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('response', {}).get('numFound', 0) > 0:
                return True
    except Exception as e:
        pass
    return False

def main():
    anatomy_count = 0
    with gzip.open('tasks/human_anatomy/chunk-0013.csv.gz', 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        subjects = [row['subject_name'] for row in reader]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_ols, subjects))

    for subject, is_anatomy in zip(subjects, results):
        if is_anatomy:
            anatomy_count += 1
            print(f"Found anatomy: {subject}")

    print(f"Total anatomy found: {anatomy_count}")

if __name__ == "__main__":
    main()
