import csv
import gzip
import json
import urllib.parse
import urllib.request
import concurrent.futures

INPUT_FILE = "tasks/invertebrate/chunk-0008.csv.gz"
OUTPUT_FILE = "out/invertebrate/chunk-0008.csv"

def fetch_gbif(subject_name):
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(subject_name)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read()), url
    except Exception as e:
        return None, url

def process_row(row):
    key = row['canonical_dedup_key']
    name = row['subject_name']

    data, url = fetch_gbif(name)
    results = []
    if data and data.get('matchType') in ['EXACT', 'FUZZY'] and data.get('confidence', 0) >= 90:
        kingdom = data.get('kingdom')
        phylum = data.get('phylum')
        class_ = data.get('class')

        vertebrate_classes = ['Mammalia', 'Aves', 'Reptilia', 'Amphibia', 'Actinopterygii', 'Chondrichthyes', 'Sarcopterygii', 'Elasmobranchii', 'Myxini', 'Petromyzonti']

        if kingdom in ['Plantae', 'Fungi']:
            return results

        if class_ in vertebrate_classes:
            return results

        if kingdom == 'Animalia' and phylum == 'Chordata':
             if class_ not in ['Ascidiacea', 'Thaliacea', 'Appendicularia', 'Leptocardii']:
                 return results

        canonical = data.get('canonicalName')
        scientific = data.get('scientificName')

        if canonical:
            results.append((key, 'scientific_identity', json.dumps(canonical), url))

        if canonical and scientific and scientific.startswith(canonical) and len(scientific) > len(canonical):
            authority = scientific[len(canonical):].strip()
            if authority:
                results.append((key, 'taxon_authority', json.dumps(authority), url))

        descriptive = []
        for rank in ['phylum', 'class', 'order', 'family', 'genus']:
            if data.get(rank):
                descriptive.append(data.get(rank))
        for d in descriptive:
            results.append((key, 'descriptive_identity', json.dumps(d), url))

    return results

def main():
    rows = []
    with gzip.open(INPUT_FILE, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_row, row): row for row in rows}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            if i % 100 == 0:
                print(f"Processed {i} / {len(rows)}")
            res = future.result()
            if res:
                all_results.extend(res)

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])
        for r in all_results:
            writer.writerow(r)

    print(f"Total rows written: {len(all_results)}")

if __name__ == '__main__':
    main()
