import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0'}

ships = [
    # Submersibles
    "DSV Alvin",
    "DSV Shinkai 6500",
    "Jiaolong (submersible)",
    "Deepsea Challenger",
    "Titan (submersible)",
    "Nereus (underwater vehicle)",
    "Konsul-class submersible",
    "Mir (submersible)",
    "Piscis-class submersible",
    "Pisces IV",
    "Pisces V",
    "Limiting Factor (submersible)",

    # Specific ships with known height/depth
    "RV Sikuliaq",
    "BRP Jose Rizal",

    # Yachts / Small boats
    "A (sailing yacht)",
    "A (motor yacht)",
    "Azzam (2013 yacht)",
    "Eclipse (yacht)",
    "Dubai (yacht)",
    "Dilbar (yacht)",
    "Al Said (yacht)",

    # Lifeboats (often have all dimensions)
    "Severn-class lifeboat",
    "Tamar-class lifeboat",
    "Shannon-class lifeboat",
    "Trent-class lifeboat",

    # Specific ships that might have depth
    "MV Tønsberg",
    "CSCL Globe",
    "MSC Oscar",
    "Barzan (ship)",
    "Madrid Maersk",
    "OOCL Hong Kong",
    "Symphony of the Seas",
    "Harmony of the Seas",
    "Oasis of the Seas",
    "Allure of the Seas",

    # More Navy ships 2010-2019
    "KRI RE Martadinata",
    "BRP Tarlac (LD-601)",
    "BRP Davao del Sur (LD-602)"
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

        # search for exact year 2010-2019
        year_ok = False
        for k, v in data.items():
            if any(x in k for x in ['launched', 'commissioned', 'laid down', 'acquired', 'completed']):
                if re.search(r'\b201[0-9]\b', v):
                    year_ok = True
                    break

        if not year_ok:
            continue

        print(f"\n--- {s} ---")
        for k in ['length', 'beam', 'draft', 'draught', 'depth', 'height', 'displacement', 'tonnage', 'weight', 'launched', 'commissioned', 'laid down', 'acquired', 'completed']:
            for dk, dv in data.items():
                if k in dk:
                    print(f"{dk}: {dv}")
    except Exception as e:
        pass
    time.sleep(1)
