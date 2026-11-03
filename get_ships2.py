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
    match = re.search(r'([\d\.]+)\s*m\b', text)
    if match:
        return float(match.group(1)) * 1000
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
        return val * 1016046.91
    match = re.search(r'([\d\,]+)\s*(?:short\s+)?tons?', text)
    if match:
        val = float(match.group(1).replace(',', ''))
        return val * 907184.74
    match = re.search(r'([\d\,]+)\s*t\b', text)
    if match:
        val = float(match.group(1).replace(',', ''))
        return val * 1e6
    match = re.search(r'([\d\,]+)\s*tonnes?', text)
    if match:
        val = float(match.group(1).replace(',', ''))
        return val * 1e6
    return None

ships_list = [
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
    "KRI I Gusti Ngurah Rai",
    "ENS Tahya Misr",
    "ENS Anwar El Sadat",
    "ENS Gamal Abdel Nasser",
    "INS Rahav",
    "INS Tanin (2012)",
    "BNS Bangabandhu",
    "ENS El Fateh",
    "NNS Centenary",
    "NNS Unity",
    "NNS Karaduwa",
    "CGS Barracuda",
    "HMAS Adelaide (L01)",
    "HMAS Hobart (DDG 39)",
    "HMAS Brisbane (DDG 41)",
    "HMAS Sydney (DDG 42)",
    "HMNZS Aotearoa",
    "HMNZS Wellington (P55)",
    "RV Kronprins Haakon",
    "RRS Sir David Attenborough",
    "RSV Nuyina",
    "RV Sikuliaq"
]

for ship in ships_list:
    url = f"https://en.wikipedia.org/api/rest_v1/page/html/{urllib.parse.quote(ship)}"
    resp = requests.get(url)
    if resp.status_code != 200:
        continue
    soup = BeautifulSoup(resp.text, 'html.parser')
    infobox = soup.find('table', class_='infobox')
    if not infobox:
        continue

    data = {}
    for tr in infobox.find_all('tr'):
        th = tr.find('th')
        td = tr.find('td')
        if th and td:
            label = th.get_text(strip=True).lower()
            val = td.get_text(separator=' ', strip=True)
            data[label] = val

    print(f"\n--- {ship} ---")
    for k in ['length', 'beam', 'draft', 'draught', 'depth', 'height', 'displacement', 'tonnage', 'weight', 'launched', 'commissioned', 'laid down', 'acquired', 'completed']:
        for dk, dv in data.items():
            if k in dk:
                print(f"{dk}: {dv}")
