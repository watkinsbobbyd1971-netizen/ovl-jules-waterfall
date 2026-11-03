import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0'}

# INS Vikrant (2013) -> 2013 launched, REG_06
# L: 262500, W: 62000, H: 59000, Mass: 45,000 tonnes (45e9 g)

# Harmony of the Seas, Allure of the Seas, BRP Jose Rizal, RV Sikuliaq, Titan (submersible)

# Need 30 subjects. This is getting hard because very few ships have an explicit height and mass and fit the time/region criteria.
# Let's search specifically for ships in REG_06-REG_10 from 2010-2019 that might have depth or height.
# Container ships often have depth listed:
ships = [
    "Maersk Mc-Kinney Møller (ship)",
    "Mary Maersk",
    "Marstal Maersk",
    "Matz Maersk",
    "Mayview Maersk",
    "Merete Maersk",
    "Mogens Maersk",
    "Morten Maersk",
    "Munkebo Maersk",
    "Madison Maersk",
    "Magleby Maersk",
    "Maribo Maersk",
    "Marie Maersk",
    "Mathilde Maersk",
    "Eugen Maersk",
    "Eleonora Maersk",
    "Estelle Maersk",
    "Ebba Maersk",
    "Edith Maersk",
    "Elly Maersk",
    "Eleonora Maersk",
    "Gudrun Maersk",
    "Grete Maersk",
    "Gunvor Maersk",
    "Gerda Maersk",
    "Georg Maersk",
    "Gerd Maersk"
]

for s in ships:
    url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(s)}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
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

        has_mass = False
        has_height = False
        year_ok = False

        for k, v in data.items():
            if any(x in k for x in ['launched', 'commissioned', 'laid down', 'acquired', 'completed']):
                if re.search(r'\b201[0-9]\b', v):
                    year_ok = True

        for k,v in data.items():
            if 'displacement' in k or 'weight' in k:
                if 'tons' in v or 'tonnes' in v or 'kg' in v or 'lb' in v or ' t ' in v or ' t' in v:
                    has_mass = True
            if 'height' in k or 'depth' in k:
                has_height = True

        if has_mass and has_height and year_ok:
            print(f"\n--- {s} ---")
            for k in ['length', 'beam', 'draft', 'draught', 'depth', 'height', 'displacement', 'tonnage', 'weight', 'launched', 'commissioned', 'laid down', 'acquired', 'completed']:
                for dk, dv in data.items():
                    if k in dk:
                        print(f"{dk}: {dv}")
    except Exception:
        pass
    time.sleep(0.5)
