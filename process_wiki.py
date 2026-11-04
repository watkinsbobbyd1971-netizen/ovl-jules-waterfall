import urllib.request
import urllib.parse
import json
import gzip
import csv
import time

def fetch_with_retry(url, max_retries=5):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Bot)'})
    for i in range(max_retries):
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            if '429' in str(e):
                time.sleep((i + 1) * 2)
            else:
                return None
    return None

def main():
    in_file = "tasks/built_environment/chunk-0079.csv.gz"
    out_file = "out/built_environment/chunk-0079.csv"

    with gzip.open(in_file, 'rt') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Total rows: {len(rows)}")

    out_rows = []

    # We can batch query Wikidata using titles instead of doing wbsearchentities one by one?
    # Actually, they are town halls, not always having Wikipedia pages, but maybe they do in eswiki or enwiki.
    # What if we just do wbsearchentities with sleep?

    for idx, row in enumerate(rows[:5]):
        key = row['canonical_dedup_key']
        subject = row['subject_name']
        print(f"Processing {idx+1}/{len(rows)}: {subject}")

        search_url = "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=" + urllib.parse.quote(subject) + "&language=en&format=json"
        search_data = fetch_with_retry(search_url)

        if search_data and search_data.get('search'):
            item_id = search_data['search'][0]['id']
            url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={item_id}&format=json&props=claims|labels|descriptions"
            data = fetch_with_retry(url)

            if data and 'entities' in data and item_id in data['entities']:
                entity = data['entities'][item_id]
                claims = entity.get('claims', {})
                source_url = f"https://www.wikidata.org/wiki/{item_id}"

                labels = entity.get('labels', {})
                if 'en' in labels:
                    out_rows.append([key, 'identity_label', labels['en']['value'], source_url])

                descriptions = entity.get('descriptions', {})
                if 'en' in descriptions:
                    out_rows.append([key, 'descriptive_identity', descriptions['en']['value'], source_url])

                if 'P131' in claims:
                    for claim in claims['P131']:
                        val = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
                        if val:
                            loc_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={val}&format=json&props=labels"
                            loc_data = fetch_with_retry(loc_url)
                            if loc_data:
                                loc_label = loc_data['entities'][val].get('labels', {}).get('en', {}).get('value')
                                if loc_label:
                                    out_rows.append([key, 'location', loc_label, source_url])
        time.sleep(1)

    print(f"Found {len(out_rows)} results")
    for r in out_rows:
        print(r)

if __name__ == '__main__':
    main()
