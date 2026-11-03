import requests
import json
import re
import urllib.parse
from bs4 import BeautifulSoup
import time
import hashlib

def extract_dimension(text):
    if not text:
        return None
    # match float/int followed by m
    match = re.search(r'([\d\.]+)\s*m\b', text)
    if match:
        return float(match.group(1)) * 1000 # to mm
    # meters or metres
    match = re.search(r'([\d\.]+)\s*metre', text)
    if match:
        return float(match.group(1)) * 1000
    match = re.search(r'([\d\.]+)\s*meter', text)
    if match:
        return float(match.group(1)) * 1000
    return None

def extract_mass(text):
    if not text:
        return None
    match = re.search(r'([\d\,]+)\s*(?:long\s+)?tons?', text)
    if match:
        val = float(match.group(1).replace(',', ''))
        return val * 1016046.91 # long tons to g
    match = re.search(r'([\d\,]+)\s*(?:short\s+)?tons?', text)
    if match:
        val = float(match.group(1).replace(',', ''))
        return val * 907184.74 # short tons to g
    match = re.search(r'([\d\,]+)\s*t\b', text)
    if match:
        val = float(match.group(1).replace(',', ''))
        return val * 1e6 # tonnes to g
    match = re.search(r'([\d\,]+)\s*tonnes?', text)
    if match:
        val = float(match.group(1).replace(',', ''))
        return val * 1e6
    return None

ships_list = [
    # South & Southeast Asia (REG_06)
    "KRI Raden Eddy Martadinata",
    "BRP Antonio Luna",
    "BNS Prottasha",
    "KRI Ardadedali",
    "Vietnamese research ship Tran Dai Nghia",
    "KRI Teluk Palu",
    "MV Dali",
    "INS Vikramaditya",
    "KRI Teluk Bintuni",
    "KRI Teluk Lada",
    "KRI Nagapasa",
    "KRI Alugoro",
    "BRP Jose Rizal",
    "KRI Tarakan (905)",
    "KRI Bima Suci",
    "UMS Minye Theinkhathu",
    "BNS Shadhinota",
    "BNS Prottoy",
    "HTMS Krabi",
    "HTMS Prachuap Khiri Khan",
    "KRI RE Martadinata",
    "KRI I Gusti Ngurah Rai",

    # Middle East & North Africa (REG_07)
    "ENS Tahya Misr",
    "ENS Anwar El Sadat",
    "ENS Gamal Abdel Nasser",
    "INS Rahav",
    "INS Tanin (2012)",
    "BNS Bangabandhu",
    "MV Dar Tanga",
    "ENS El Fateh",

    # Sub-Saharan Africa (REG_08)
    "S A Agulhas II",
    "NNS Centenary",
    "NNS Unity",
    "NNS Karaduwa",
    "CGS Barracuda",

    # Oceania & Pacific (REG_09)
    "HMAS Canberra (L02)",
    "RV Investigator",
    "HMAS Adelaide (L01)",
    "HMAS Hobart (DDG 39)",
    "HMAS Brisbane (DDG 41)",
    "HMAS Sydney (DDG 42)",
    "HMNZS Aotearoa",
    "HMNZS Wellington (P55)",
    "FSS Micronesia",
    "NSS Tosiwo Nakayama",

    # Polar, Oceanic & Orbital (REG_10)
    "RV Kronprins Haakon",
    "RRS Sir David Attenborough",
    "RSV Nuyina",
    "RV Sikuliaq"
]

def fetch_wiki_infobox(title):
    url = f"https://en.wikipedia.org/api/rest_v1/page/html/{urllib.parse.quote(title)}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.text, 'html.parser')
    infobox = soup.find('table', class_='infobox')
    if not infobox:
        return None
    data = {}
    for tr in infobox.find_all('tr'):
        th = tr.find('th')
        td = tr.find('td')
        if th and td:
            label = th.get_text(strip=True).lower()
            val = td.get_text(separator=' ', strip=True)
            data[label] = val

    # look for year
    year = None
    for k, v in data.items():
        if 'launched' in k or 'commissioned' in k or 'laid down' in k or 'acquired' in k or 'completed' in k:
            m = re.search(r'\b(201[0-9])\b', v)
            if m:
                year = int(m.group(1))
                break

    length_mm = None
    width_mm = None
    height_mm = None
    mass_g = None

    for k, v in data.items():
        if 'length' in k:
            l = extract_dimension(v)
            if l: length_mm = l
        if 'beam' in k or 'width' in k:
            w = extract_dimension(v)
            if w: width_mm = w
        if 'draft' in k or 'draught' in k or 'height' in k or 'depth' in k:
            h = extract_dimension(v)
            if h: height_mm = h
        if 'displacement' in k or 'tonnage' in k or 'weight' in k:
            m = extract_mass(v)
            if m: mass_g = m

    # For ships, Draft doesn't equal Height.
    # Height must be explicitly stated. If only draft is stated, height_mm is missing.
    # Let's search for height/depth explicitly.
    height_mm = None
    for k, v in data.items():
        if 'height' in k or 'depth' in k:
            h = extract_dimension(v)
            if h: height_mm = h

    if year and length_mm and width_mm and height_mm and mass_g:
        return {
            'year': year,
            'length_mm': length_mm,
            'width_mm': width_mm,
            'height_mm': height_mm,
            'mass_g': mass_g,
            'url': f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
            'mass_basis': 'SOURCED'
        }
    return None

import json

for ship in ships_list:
    res = fetch_wiki_infobox(ship)
    if res:
        print(f"Found valid: {ship} -> {json.dumps(res)}")
    time.sleep(0.1)
