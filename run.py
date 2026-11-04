import urllib.request
import urllib.parse
import json
import csv
import gzip
import time
import os
import concurrent.futures

# Wikidata properties map to our columns
PROPERTY_MAP = {
    "P527": "component_relationship",    # has part
    "P31": "descriptive_identity",       # instance of
    "P279": "descriptive_identity",      # subclass of
    "P2043": "dimension_length",         # length
    "P176": "manufacturer_or_creator",   # manufacturer
    "P170": "manufacturer_or_creator",   # creator
    "P2067": "mass",                     # mass
    "P186": "material_identity",         # material used
    "P2102": "rated_power",              # rated power
}

# Cache for entity labels
label_cache = {}

def search_wikidata(query):
    # Try exact match first
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "format": "json",
        "limit": 5
    })
    req = urllib.request.Request(url, headers={"User-Agent": "MyBot/1.0 (https://example.org/mybot) bot@example.org"})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "search" in data:
                for match in data["search"]:
                    if match["label"].lower() == query.lower():
                        return match["id"]
    except Exception as e:
        pass
    return None

def resolve_entity_labels(entity_ids):
    # Resolve multiple entity IDs in one batch
    uncached_ids = [eid for eid in entity_ids if eid not in label_cache]

    if not uncached_ids:
        return

    # Batch resolve up to 50 at a time
    for i in range(0, len(uncached_ids), 50):
        batch = uncached_ids[i:i+50]
        url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "labels",
            "languages": "en",
            "format": "json"
        })
        req = urllib.request.Request(url, headers={"User-Agent": "MyBot/1.0 (https://example.org/mybot) bot@example.org"})
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                if "entities" in data:
                    for eid, entity_data in data["entities"].items():
                        labels = entity_data.get("labels", {})
                        if "en" in labels:
                            label_cache[eid] = labels["en"]["value"]
                        else:
                            label_cache[eid] = eid # fallback
        except Exception as e:
            for eid in batch:
                if eid not in label_cache:
                    label_cache[eid] = eid

def resolve_entity_label(entity_id):
    if entity_id not in label_cache:
        resolve_entity_labels([entity_id])
    return label_cache.get(entity_id, entity_id)

def main():
    input_file = "tasks/electronics/chunk-0013.csv.gz"
    output_file = "out/electronics/chunk-0013.csv"
    notes_file = "out/electronics/chunk-0013.notes.txt"

    subjects = []
    with gzip.open(input_file, 'rt', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subjects.append(row)

    print(f"Total subjects: {len(subjects)}")

    # 1. Search for entity IDs (concurrently)
    entity_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_subject = {executor.submit(search_wikidata, s['subject_name']): s for s in subjects}
        for future in concurrent.futures.as_completed(future_to_subject):
            s = future_to_subject[future]
            try:
                eid = future.result()
                if eid:
                    entity_map[s['subject_name']] = eid
            except Exception:
                pass

    print(f"Found {len(entity_map)} Wikidata entities.")

    # 2. Get claims for all found entities
    claims_map = {}
    # Batch getentities up to 50 at a time
    eids = list(entity_map.values())
    for i in range(0, len(eids), 50):
        batch = eids[i:i+50]
        url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "claims",
            "format": "json"
        })
        req = urllib.request.Request(url, headers={"User-Agent": "MyBot/1.0 (https://example.org/mybot) bot@example.org"})
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                if "entities" in data:
                    for eid, edata in data["entities"].items():
                        claims_map[eid] = edata.get("claims", {})
        except Exception:
            pass

    print(f"Retrieved claims for {len(claims_map)} entities.")

    # 3. Collect all target IDs needed for label resolution
    target_ids = set()
    for eid, claims in claims_map.items():
        for prop, claims_list in claims.items():
            if prop in PROPERTY_MAP:
                for claim in claims_list:
                    mainsnak = claim.get("mainsnak", {})
                    if mainsnak.get("snaktype") == "value":
                        datavalue = mainsnak.get("datavalue", {})
                        if datavalue.get("type") == "wikibase-entityid":
                            target_id = datavalue.get("value", {}).get("id")
                            if target_id:
                                target_ids.add(target_id)

    print(f"Found {len(target_ids)} target entities to resolve labels for.")
    resolve_entity_labels(list(target_ids))
    print("Resolved target labels.")

    # 4. Extract values
    all_results = []
    for s in subjects:
        subj_name = s['subject_name']
        dedup_key = s['canonical_dedup_key']
        eid = entity_map.get(subj_name)
        if not eid:
            continue

        claims = claims_map.get(eid, {})
        source_url = f"https://www.wikidata.org/wiki/{eid}"

        for prop, claims_list in claims.items():
            if prop in PROPERTY_MAP:
                col_name = PROPERTY_MAP[prop]
                for claim in claims_list:
                    mainsnak = claim.get("mainsnak", {})
                    if mainsnak.get("snaktype") == "value":
                        datavalue = mainsnak.get("datavalue", {})
                        datatype = datavalue.get("type")
                        value = datavalue.get("value")

                        if datatype == "wikibase-entityid" and isinstance(value, dict):
                            target_id = value.get("id")
                            if target_id:
                                label = resolve_entity_label(target_id)
                                all_results.append({
                                    "canonical_dedup_key": dedup_key,
                                    "column_name": col_name,
                                    "value": json.dumps(label),
                                    "source_url": source_url
                                })
                        elif datatype == "quantity" and isinstance(value, dict):
                            amount = value.get("amount")
                            unit_url = value.get("unit")
                            if amount:
                                amount_val = float(amount.replace('+', ''))
                                if col_name == "dimension_length":
                                    if "Q174728" in unit_url: # cm -> mm
                                        amount_val *= 10
                                    elif "Q11573" in unit_url: # m -> mm
                                        amount_val *= 1000
                                    elif "Q218593" in unit_url: # inch -> mm
                                        amount_val *= 25.4
                                    all_results.append({
                                        "canonical_dedup_key": dedup_key,
                                        "column_name": col_name,
                                        "value": json.dumps(amount_val),
                                        "source_url": source_url
                                    })
                                elif col_name == "mass":
                                    if "Q11570" in unit_url: # kg -> g
                                        amount_val *= 1000
                                    all_results.append({
                                        "canonical_dedup_key": dedup_key,
                                        "column_name": col_name,
                                        "value": json.dumps(amount_val),
                                        "source_url": source_url
                                    })
                                elif col_name == "rated_power":
                                    if "Q25343" in unit_url: # kW -> W
                                        amount_val *= 1000
                                    all_results.append({
                                        "canonical_dedup_key": dedup_key,
                                        "column_name": col_name,
                                        "value": json.dumps(amount_val),
                                        "source_url": source_url
                                    })

    # 5. Deduplicate and write
    unique_results = []
    seen = set()
    for r in all_results:
        key = (r['canonical_dedup_key'], r['column_name'], r['value'])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["canonical_dedup_key", "column_name", "value", "source_url"], quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in unique_results:
            writer.writerow(r)

    with open(notes_file, 'w', encoding='utf-8') as f:
        f.write("Queried Wikidata Action API for entities and their claims (instance of, subclass of, has part, manufacturer, creator, length, mass, rated power). Filtered exact matches.\n")

    print(f"Done! Extracted {len(unique_results)} values.")

if __name__ == "__main__":
    main()
