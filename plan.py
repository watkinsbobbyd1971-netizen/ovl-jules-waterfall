import urllib.request
import urllib.parse
import json
import gzip
import csv
import re
import os
import concurrent.futures

def get_gbif_mammals():
    mammals_to_match = []
    with gzip.open('tasks/mammal/chunk-0014.csv.gz', 'rt') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) > 1:
                key, subject = row[0], row[1]
                clean_sub = subject.strip('"').strip("'").strip()
                clean_sub = re.sub(r' \([^)]*\)', '', clean_sub).strip()
                mammals_to_match.append((key, clean_sub))

    def fetch_gbif(item):
        key, name = item
        words = name.split()
        if not words: return None
        if len(words) > 4: return None

        names_to_try = [name]
        if len(words) >= 2 and words[0][0].isupper():
            names_to_try.append(f"{words[0]} {words[1]}")
        if len(words) >= 3 and words[0][0].isupper():
            names_to_try.append(f"{words[0]} {words[1]} {words[2]}")

        if "Drill Fragment" in name:
            names_to_try.append("Drill")

        results = []
        for n in names_to_try:
            url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(n)}&class=Mammalia"
            req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get('matchType') == 'EXACT' and data.get('class') == 'Mammalia':
                        results.append((key, n, data))
                        break
            except:
                pass
        return results if results else None

    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_gbif, mammals_to_match))
        for r in results:
            if r:
                found.extend(r)

    return found

def run():
    print("Fetching GBIF matches...")
    gbif_matched = get_gbif_mammals()
    print(f"Matched {len(gbif_matched)} items from GBIF")

    os.makedirs('out/mammal', exist_ok=True)
    with open('out/mammal/chunk-0014.csv', 'w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])

        for key, name, data in gbif_matched:
            usage_key = data.get('usageKey')
            if not usage_key:
                continue

            source_url = f"https://www.gbif.org/species/{usage_key}"

            sci_name = data.get('scientificName')
            if sci_name:
                writer.writerow([key, 'scientific_identity', json.dumps(sci_name), source_url])

            taxon_auth = data.get('authorship')
            if taxon_auth:
                writer.writerow([key, 'taxon_authority', json.dumps(taxon_auth), source_url])

            ranks = []
            for rank in ['kingdom', 'phylum', 'class', 'order', 'family', 'genus']:
                if data.get(rank):
                    ranks.append(data.get(rank))
            if ranks:
                writer.writerow([key, 'descriptive_identity', json.dumps(" > ".join(ranks)), source_url])

run()
