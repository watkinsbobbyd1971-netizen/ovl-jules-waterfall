import csv
import gzip
import json
import urllib.request
import urllib.parse
import sys
import re

# columns: canonical_dedup_key,column_name,value,source_url
processed = {}
no_match = set()
with open('out/reptile_fish/chunk-0024.csv', 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=['canonical_dedup_key', 'column_name', 'value', 'source_url'])
    writer.writeheader()

    def search_gbif(subject_name):
        if any(x in subject_name.lower() for x in ["axe", "stone", "rope", "bowl", "jar", "basket", "pitcher", "sculpture", "knife", "cup", "vessel"]):
            return None
        cleaned_name = re.sub(r'\(.*?\)', '', subject_name).strip()
        url = f"https://api.gbif.org/v1/species/search?q={urllib.parse.quote(cleaned_name)}&limit=3"
        req = urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0'})
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                results = data.get('results', [])
                for res in results:
                    kingdom = res.get('kingdom', '').lower()
                    class_ = res.get('class', '').lower()
                    if kingdom == 'animalia' and class_ in ['reptilia', 'actinopterygii', 'chondrichthyes', 'sarcopterygii', 'amphibia']:
                        scientific_name = res.get('scientificName')
                        authorship = res.get('authorship')
                        rank = res.get('rank')
                        vernacular = res.get('vernacularName', cleaned_name)
                        extracted = {}
                        if scientific_name:
                            extracted['scientific_identity'] = scientific_name
                        if authorship:
                            extracted['taxon_authority'] = authorship
                        if rank:
                            extracted['descriptive_identity'] = rank
                        extracted['identity_label'] = vernacular
                        return extracted, url
        except Exception:
            pass
        return None

    with gzip.open('tasks/reptile_fish/chunk-0024.csv.gz', 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            key = row['canonical_dedup_key']
            name = row['subject_name']

            if name in processed:
                extracted, url = processed[name]
            elif name in no_match:
                continue
            else:
                result = search_gbif(name)
                if result:
                    processed[name] = result
                    extracted, url = result
                else:
                    no_match.add(name)
                    continue

            for col, val in extracted.items():
                writer.writerow({
                    'canonical_dedup_key': key,
                    'column_name': col,
                    'value': json.dumps(val) if isinstance(val, str) else str(val),
                    'source_url': url
                })

            if i % 100 == 0:
                print(f"Processed {i} rows")

print(f"Total matched subjects: {len(processed)}")
