import urllib.request
import json
import re
import os
import hashlib
import time

def parse_mass_2(val_str):
    if not val_str: return None

    for m in re.finditer(r'{{convert\s*\|\s*([\d\.,]+)\s*\|\s*([a-zA-Z]+)', val_str, re.IGNORECASE):
        try:
            v = float(m.group(1).replace(',', ''))
            u = m.group(2).lower()
            if u in ['t', 'tonne', 'tonnes']: return v * 1_000_000
            if u in ['kg']: return v * 1000
            if u in ['lb', 'lbs']: return v * 453.592
            if u in ['lt', 'long ton', 'long tons']: return v * 1_016_047
        except:
            pass

    m = re.search(r'([\d\.,]+)\s*(?:t|tonnes?|tons?)\b', val_str)
    if m: return float(m.group(1).replace(',', '')) * 1_000_000
    m = re.search(r'([\d\.,]+)\s*(?:kg|kilograms?)\b', val_str)
    if m: return float(m.group(1).replace(',', '')) * 1000
    m = re.search(r'([\d\.,]+)\s*(?:lb|lbs|pounds?)\b', val_str)
    if m: return float(m.group(1).replace(',', '')) * 453.592

    return None

def parse_dim_2(val_str):
    if not val_str: return None

    for m in re.finditer(r'{{convert\s*\|\s*([\d\.,]+)\s*\|\s*([a-zA-Z]+)', val_str, re.IGNORECASE):
        try:
            v = float(m.group(1).replace(',', ''))
            u = m.group(2).lower()
            if u == 'm': return v * 1000
            if u == 'cm': return v * 10
            if u == 'mm': return v
            if u == 'ft': return v * 304.8
            if u == 'in': return v * 25.4
        except:
            pass

    m = re.search(r'([\d\.,]+)\s*(?:m|metres|meters)\b', val_str)
    if m: return float(m.group(1).replace(',', '')) * 1000
    m = re.search(r'([\d\.,]+)\s*(?:cm|centimetres|centimeters)\b', val_str)
    if m: return float(m.group(1).replace(',', '')) * 10
    m = re.search(r'([\d\.,]+)\s*(?:mm|millimetres|millimeters)\b', val_str)
    if m: return float(m.group(1).replace(',', ''))

    m = re.search(r'([\d\.,]+)\s*(?:ft|feet)\b', val_str)
    if m: return float(m.group(1).replace(',', '')) * 304.8
    m = re.search(r'([\d\.,]+)\s*(?:in|inches)\b', val_str)
    if m: return float(m.group(1).replace(',', '')) * 25.4

    return None

def get_prop(infobox, prop_name):
    m = re.search(r'\|\s*' + prop_name + r'\s*=\s*(.*?)\n(?:\||}})', infobox, re.IGNORECASE | re.DOTALL)
    if m: return m.group(1).strip()
    return None

def extract_infobox(text):
    if not text: return None
    lines = text.split('\n')
    in_box = False
    box_lines = []
    brackets = 0
    for line in lines:
        if '{{Infobox' in line and not in_box:
            in_box = True
            brackets += line.count('{{') - line.count('}}')
            box_lines.append(line)
        elif in_box:
            brackets += line.count('{{') - line.count('}}')
            box_lines.append(line)
            if brackets <= 0:
                break
    if box_lines:
        return '\n'.join(box_lines)
    return None

def get_page_info_rest(page_name):
    # Try DuckDuckGo
    time.sleep(1)
    url = f"https://html.duckduckgo.com/html/?q=site:en.wikipedia.org+{urllib.parse.quote(page_name)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        links = re.findall(r'href="([^"]+)"', html)
        urls = [urllib.parse.unquote(l.split('uddg=')[1].split('&')[0]) for l in links if 'uddg=' in l and 'wikipedia.org/wiki/' in l]
        if not urls: return None
        wiki_url = urls[0]
        # Instead of Wikipedia, try using duckduckgo cache/extract or just wikitext API for that exact extracted title
        title = wiki_url.split('/wiki/')[-1]

        # fallback to text dump
        url2 = f"https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&titles={title}&format=json"
        req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        response = urllib.request.urlopen(req2).read().decode('utf-8')
        data = json.loads(response)
        pages = data['query']['pages']
        for page_id in pages:
            if page_id == "-1": return None
            return pages[page_id]['revisions'][0]['*']
    except:
        return None

subjects = [
    {"name": "INS Vikrant (2013)", "region": "REG_06", "year": 2022},
    {"name": "HAL Prachand", "region": "REG_06", "year": 2022},
    {"name": "BRP Antonio Luna (FF-151)", "region": "REG_06", "year": 2021},
    {"name": "BRP Jose Rizal (FF-150)", "region": "REG_06", "year": 2020},
    {"name": "PNS Badr (F281)", "region": "REG_06", "year": 2022},
    {"name": "KRI Golok (688)", "region": "REG_06", "year": 2021},
    {"name": "INS Himgiri", "region": "REG_06", "year": 2020},
    {"name": "INS Taragiri", "region": "REG_06", "year": 2022},
    {"name": "PNS Tariq (F283)", "region": "REG_06", "year": 2023},
    {"name": "Sa'ar 6-class corvette", "region": "REG_07", "year": 2020},
    {"name": "Type 054A/P frigate", "region": "REG_06", "year": 2021},
    {"name": "Ada-class corvette", "region": "REG_07", "year": 2023}
]

valid_data = []

# Wait, 76 mm is 7.6 cm! This looks like gun caliber for "PNS Shah Jahan (F264)".
# Let me look at the mass: 219 grams.
# It parsed a 76 mm gun and used it as length, width and height!
