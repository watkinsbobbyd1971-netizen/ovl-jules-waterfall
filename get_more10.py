import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0'}

# Nereus: length 3m, mass 2800 kg (does not have height/width) -> SKIP
# Boaty McBoatface: length 3.62m, mass 700 kg (does not have height/width) -> SKIP
# Shinkai 6500: L/W/Draft (no mass, no explicit height) -> SKIP

# Okay, what about larger ships with depth again?
ships = [
    "MV Taiko", # sunk/scrapped, what era?
    "Symphony of the Seas",
    "MSC Seaview",
    "MSC Seaside",
    "MSC Meraviglia",
    "Norwegian Joy",
    "Carnival Horizon",
    "Carnival Vista",
    "MS Iona", # 2020?
    "P&O Britannia", # 2015
    "Majestic Princess",
    "Norwegian Escape"
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

        print(f"\n--- {s} ---")
        for k in ['length', 'beam', 'draft', 'draught', 'depth', 'height', 'displacement', 'tonnage', 'weight', 'mass', 'launched', 'commissioned', 'laid down', 'acquired', 'completed', 'diameter']:
            for dk, dv in data.items():
                if k in dk:
                    print(f"{dk}: {dv}")
    except Exception:
        pass
    time.sleep(0.5)
