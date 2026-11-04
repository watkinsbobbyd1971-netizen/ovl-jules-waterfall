#!/usr/bin/env python3
"""Check one output file against the rules in CORPUS-RULES.md before you commit it. Standard library only.

  python3 check_output.py out/<category>/chunk-NNNN.csv         lists every problem; exit 0 means ready to commit
  python3 check_output.py out/<category>/chunk-NNNN.csv --fix   corrects value form, removes every row that still fails, rewrites the file

These are the same checks the file meets after you push. A removed row is the right outcome when you can't
source it: an empty cell can be filled later, and a wrong one can't be told from a right one."""
import argparse
import collections
import csv
import gzip
import json
import math
from pathlib import Path
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

csv.field_size_limit(1 << 30)
HEADER = ['canonical_dedup_key', 'column_name', 'value', 'source_url']
# Only a service that didn't answer. These rows pass here and get checked again after the push.
NOT_CHECKED = {'source_not_checked', 'numeric_not_checked'}
MECHANICAL = {'plain_text_in_json_column', 'number_in_string_column', 'string_in_number_column', 'single_item_array',
              'double_encoded', 'duplicate_exact'}
SOURCE_LIST = re.compile(r'getmodels|/search\b|/sparql\b|[?&](?:q|query|search|srsearch|filter|limit|offset|page)=|/list\b|/match\b'
                         r'|/wiki/(?:List_of|Lists_of|Category:|Special:)', re.I)
SOURCE_FABRICATED = re.compile(r'wikipedia\.org/wiki/CAT_\d|[?&#]rec=\d')
UNIT_IN_VALUE = re.compile(r'^\s*[-+]?\d[\d,.]*\s*[a-zA-Z"\']+\s*$')
PLACEHOLDER = {'unknown', 'n/a', 'na', 'none', 'null', 'tbd', 'not available', 'not applicable', 'various', 'unspecified', '-', '?'}
STOPWORDS = {'the', 'a', 'an', 'of', 'and', 'de', 'la', 'le', 'in', 'on', 'for'}
IDENTITY_COLUMNS = {'scientific_identity', 'identity_label', 'model_identifier'}
UNITS = {'Q11573': 1000.0, 'Q828224': 1e6, 'Q174728': 10.0, 'Q174789': 1.0, 'Q3710': 304.8, 'Q218593': 25.4,
         'Q11570': 1000.0, 'Q41803': 1.0, 'Q191118': 1e6, 'Q100995': 453.59237, 'Q25236': 1.0, 'Q6859': 1000.0}
COLUMN_PROPERTIES = {
    'dimension_length': {'P2043': 'length', 'P2048': 'height', 'P2049': 'width', 'P2386': 'diameter', 'P2610': 'thickness', 'P5524': 'horizontal_depth'},
    'mass': {'P2067': 'mass'}, 'span': {'P2050': 'span'}, 'draft': {'P2262': 'draft'},
    'rail_gauge': {'P1064': 'rail_gauge'}, 'rated_power': {'P2109': 'rated_power'}, 'wingspan': {'P2050': 'wingspan'},
}
EXPECTED_KIND = {'dimension_length': 'length'}
BIOLOGY = {'mammal', 'bird', 'reptile_fish', 'invertebrate', 'fungal_microbe', 'plant'}
TAXON = {'Q16521', 'Q55983715', 'Q23038290'}
NOT_THIS_THING = {'Q4167410': 'a disambiguation page', 'Q5': 'a person'}


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check_value(raw, wants_number):
    """(problem, mechanical replacement or None); problem is None when the form is right."""
    if raw is None or not raw.strip():
        return 'empty_value', None
    try:
        parsed = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except ValueError:
        if wants_number:
            return ('unit_in_value' if UNIT_IN_VALUE.match(raw) else 'not_a_number'), None
        return 'plain_text_in_json_column', json.dumps(raw, ensure_ascii=False)
    if isinstance(parsed, list):
        if not parsed:
            return 'empty_value', None
        if len(parsed) > 1:
            return 'multi_item_array', None
        inner = parsed[0]
        if isinstance(inner, str) and not wants_number and inner.strip():
            return 'single_item_array', json.dumps(inner, ensure_ascii=False)
        if number(inner) and wants_number:
            return 'single_item_array', json.dumps(inner)
        return 'wrong_json_type', None
    if isinstance(parsed, (dict, bool)) or parsed is None:
        return 'wrong_json_type', None
    if wants_number:
        if isinstance(parsed, str):
            try:
                value = float(parsed)
            except ValueError:
                return ('unit_in_value' if UNIT_IN_VALUE.match(parsed) else 'not_a_number'), None
            return ('not_a_number', None) if not math.isfinite(value) else ('string_in_number_column', parsed.strip())
        return None, None
    if number(parsed):
        return 'number_in_string_column', json.dumps(str(parsed), ensure_ascii=False)
    if not parsed.strip():
        return 'empty_value', None
    if len(parsed) >= 2 and parsed[0] == '"' and parsed[-1] == '"':
        return 'double_encoded', json.dumps(parsed[1:-1], ensure_ascii=False)
    if parsed.strip().casefold() in PLACEHOLDER:
        return 'placeholder_value', None
    return None, None


def classify_source(url):
    """(entity or None, problem or None) for one source_url."""
    url = (url or '').strip()
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.netloc:
        return None, 'source_missing'
    if SOURCE_FABRICATED.search(url) or parts.path in ('', '/'):
        return None, 'source_fabricated_pattern'
    host = parts.netloc.lower()
    if host.endswith('wikidata.org'):
        match = re.search(r'/(?:entity|wiki|wiki/Special:EntityData)/(Q\d+)', parts.path)
        return (f'wikidata:{match[1]}', None) if match else (None, 'source_is_list')
    if host == 'drive.google.com':
        return None, 'source_not_public_record'
    if host == 'api.gbif.org':
        match = re.search(r'/species/(\d+)', parts.path)
        return (f'gbif:{match[1]}', None) if match else (None, 'source_is_list')
    if SOURCE_LIST.search(url):
        return None, 'source_is_list'
    return url.split('#')[0].rstrip('/'), None


def tokens(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).casefold()
    return {t for t in re.findall(r'[a-z0-9]+', text) if t not in STOPWORDS}


def plain_text(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).casefold()
    return ' '.join(re.findall(r'[^\W_]+', text))


def label_copy(raw, subject):
    """True when a cell only repeats the row's subject_name: padding, not data."""
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        value = raw
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    return isinstance(value, str) and bool(plain_text(value)) and plain_text(value) == plain_text(subject)


def same_subject(subject, names):
    """True, False, or None when there is nothing to compare."""
    left = tokens(subject)
    names = [n for n in (tokens(n) for n in names if n) if n]
    if not left or not names:
        return None
    return any(left <= right or right <= left or len(left & right) / len(left | right) >= 0.5 for right in names)


def fetch_wikidata(ids, opener=urllib.request.urlopen, pause=1.0):
    """The cited entities' names, classes and numbers. A batch that fails is reported, never guessed."""
    found, ids = {}, sorted(ids)
    for start in range(0, len(ids), 50):
        url = 'https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode({
            'action': 'wbgetentities', 'format': 'json', 'props': 'labels|aliases|claims', 'languages': 'en',
            'ids': '|'.join(ids[start:start + 50])})
        request = urllib.request.Request(url, headers={'User-Agent': 'corpus-check/1.0 (open data check)'})
        entities = None
        for attempt in range(3):
            try:
                with opener(request, timeout=60) as response:
                    entities = json.load(response).get('entities', {})
                break
            except urllib.error.HTTPError as exc:
                # A busy public service: wait as it asks, a few times, then report these as not checked.
                if exc.code != 429 or not pause:
                    break
                time.sleep(min(60, int(exc.headers.get('Retry-After') or 10)))
            except Exception:
                break
        if entities is None:
            continue
        for qid, entity in entities.items():
            if 'missing' in entity:
                found[qid] = {'missing': True}
                continue
            claims, classes = {}, set()
            for prop, statements in (entity.get('claims') or {}).items():
                for statement in statements:
                    value = (statement.get('mainsnak') or {}).get('datavalue', {}).get('value')
                    if prop == 'P31' and isinstance(value, dict):
                        classes.add(value.get('id'))
                    elif isinstance(value, dict) and 'amount' in value:
                        claims.setdefault(prop, []).append((float(value['amount']), value.get('unit', '').rsplit('/', 1)[-1]))
            found[qid] = {'label': (entity.get('labels') or {}).get('en', {}).get('value'),
                          'aliases': [a['value'] for a in (entity.get('aliases') or {}).get('en', [])],
                          'claims': claims, 'classes': classes}
        if pause and start + 50 < len(ids):
            time.sleep(pause)
    return found


def check_claims(column, value, entity):
    """One number against what the cited entity states."""
    properties = COLUMN_PROPERTIES.get(column)
    if not properties or not number(value):
        return None
    stated, raw_match, unknown = 0, False, 0
    for prop, kind in properties.items():
        for amount, unit in entity['claims'].get(prop, []):
            stated += 1
            factor = UNITS.get(unit)
            unknown += not factor
            if factor and math.isclose(amount * factor, value, rel_tol=0.005):
                return None if kind == EXPECTED_KIND.get(column, kind) else f'{kind}_as_length'
            raw_match = raw_match or math.isclose(amount, value, rel_tol=0.005)
    if raw_match:
        return 'unit_mismatch'
    return 'source_unit_unknown' if stated and unknown == stated else 'value_not_in_source'


def load_inputs(path):
    path = Path(path)
    match = re.search(r'out/([^/]+)/(chunk-\d+)\.csv$', path.as_posix())
    if not match:
        raise SystemExit('expected out/<category>/chunk-NNNN.csv')
    category, chunk = match.groups()
    root = Path(str(path.resolve()).rsplit('/out/', 1)[0])
    with gzip.open(root / 'tasks' / category / f'{chunk}.csv.gz', 'rt', newline='', encoding='utf-8') as stream:
        subjects = {r['canonical_dedup_key']: r.get('subject_name', '') for r in csv.DictReader(stream)}
    with (root / 'COLUMNS.csv').open(newline='', encoding='utf-8') as stream:
        columns = {r['column_name']: r for r in csv.DictReader(stream)}
    skip_path = root / 'SKIP_COLUMNS.txt'
    skip = {line.strip() for line in skip_path.read_text().splitlines() if line.strip()} if skip_path.exists() else set()
    return category, subjects, columns, skip


def check_rows(rows, category, subjects, columns, skip, opener=urllib.request.urlopen, pause=1.0):
    """{row index: [problems]} and {row index: fixed value}."""
    flags, fixes = collections.defaultdict(list), {}
    seen, entities_of_key, keys_of_entity, entity_of = collections.defaultdict(list), collections.defaultdict(set), collections.defaultdict(set), {}
    for i, row in enumerate(rows):
        seen[(row['canonical_dedup_key'], row['column_name'])].append(i)
        entity, problem = classify_source(row['source_url'])
        if problem:
            flags[i].append(problem)
        if entity:
            entity_of[i] = entity
            entities_of_key[row['canonical_dedup_key']].add(entity)
            keys_of_entity[entity].add(row['canonical_dedup_key'])
    wanted = {e.split(':')[1] for e in entity_of.values() if e.startswith('wikidata:')}
    wikidata = fetch_wikidata(wanted, opener, pause) if wanted else {}
    for i, row in enumerate(rows):
        key, column, raw = row['canonical_dedup_key'], row['column_name'], row['value']
        spec = columns.get(column)
        if key not in subjects:
            flags[i].append('key_not_in_task')
        if not spec:
            flags[i].append('unknown_column')
        elif column in skip:
            flags[i].append('column_already_filled_by_bulk')
        else:
            problem, fixed = check_value(raw, 'number' in (spec.get('description') or ''))
            if problem:
                flags[i].append(problem)
            if fixed is not None:
                fixes[i] = fixed
        same = seen[(key, column)]
        if len(same) > 1:
            different = len({rows[j]['value'].strip() for j in same}) > 1
            if different:
                flags[i].append('duplicate_conflict')
            elif i != same[0]:
                flags[i].append('duplicate_exact')
        subject = subjects.get(key, '')
        if label_copy(raw, subject):
            flags[i].append('label_copy')
        entity = entity_of.get(i)
        if len(entities_of_key.get(key, ())) > 1:
            flags[i].append('key_cites_two_entities')
        match = None
        if entity and entity.startswith('wikidata:'):
            qid = entity.split(':')[1]
            record = wikidata.get(qid)
            if record is None:
                flags[i].append('numeric_not_checked' if column in COLUMN_PROPERTIES else 'source_not_checked')
            elif record.get('missing'):
                flags[i].append('source_not_entity')
            else:
                match = same_subject(subject, [record.get('label')] + record.get('aliases', []))
                classes = record['classes']
                if category in BIOLOGY and classes and not classes & TAXON:
                    flags[i].append('wrong_class')
                elif category not in BIOLOGY and classes & TAXON:
                    flags[i].append('wrong_class')
                elif classes & set(NOT_THIS_THING):
                    flags[i].append('wrong_class')
                try:
                    value = json.loads(raw)
                except ValueError:
                    value = None
                claim = check_claims(column, value, record)
                if claim:
                    flags[i].append(claim)
        elif column in IDENTITY_COLUMNS and subject:
            try:
                text = json.loads(raw)
            except ValueError:
                text = raw
            words = tokens(str(text))
            if words and tokens(subject) and not words & tokens(subject):
                match = False
        if match is False:
            flags[i].append('subject_mismatch')
        if entity and len(keys_of_entity[entity]) > 1:
            names = sorted((subjects.get(k, '') for k in keys_of_entity[entity] if subjects.get(k)), key=len)
            if names and not all(same_subject(names[0], [other]) is not False for other in names[1:]):
                flags[i].append('one_to_many_conflict')
    return flags, fixes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file')
    parser.add_argument('--fix', action='store_true', help='correct value form, remove every row that still fails, rewrite the file')
    args = parser.parse_args(argv)
    category, subjects, columns, skip = load_inputs(args.file)
    with open(args.file, newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != HEADER:
            print('header must be exactly: ' + ','.join(HEADER))
            return 1
        rows = list(reader)
    flags, fixes = check_rows(rows, category, subjects, columns, skip)
    counts = collections.Counter(p for problems in flags.values() for p in problems)
    unchecked = sum(bool(set(problems) & NOT_CHECKED) for problems in flags.values())
    flags = {i: [p for p in problems if p not in NOT_CHECKED] for i, problems in flags.items()}
    flags = {i: problems for i, problems in flags.items() if problems}
    if args.fix:
        kept = []
        for i, row in enumerate(rows):
            if set(flags.get(i, ())) <= MECHANICAL and 'duplicate_exact' not in flags.get(i, ()):
                kept.append({**row, 'value': fixes.get(i, row['value'])})
        with open(args.file, 'w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, HEADER, lineterminator='\n')
            writer.writeheader()
            writer.writerows(kept)
        print(json.dumps({'rows_before': len(rows), 'rows_kept': len(kept), 'rows_removed': len(rows) - len(kept), 'problems': counts}))
        print('Rerun without --fix. If the file is now empty, commit the header plus a notes file saying what you tried.')
        return 0
    for i in sorted(flags)[:200]:
        print(f"line {i + 2} {rows[i]['canonical_dedup_key']} {rows[i]['column_name']}: {', '.join(flags[i])}")
    print(json.dumps({'rows': len(rows), 'rows_with_problems': len(flags), 'rows_not_checked': unchecked, 'problems': counts}))
    print('READY: commit this file' if not flags else 'NOT READY: fix these rows, or run with --fix to remove what still fails')
    return 1 if flags else 0


if __name__ == '__main__':
    sys.exit(main())
