import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0'}

ships = [
    "Symphony of the Seas",
    "Costa Smeralda (ship)",
    "AIDAnova",
    "Norwegian Encore",
    "Norwegian Bliss",
    "Norwegian Joy",
    "Carnival Panorama",
    "BRP Jose Rizal",
    "RV Sikuliaq",
    "Titan (submersible)",
    "A (sailing yacht)",
    "Harmony of the Seas",
    "Allure of the Seas"
]

# We need length, width(beam), height(depth/height) AND MASS
# Ships usually list displacement for mass.
# GT, NT, DWT are NOT mass. They are tonnage (volume/capacity).
# Symphony: no displacement.
# Costa Smeralda: no displacement.
# AIDAnova: displacement 87306 tons.
# Norwegian Encore: no displacement.
# Carnival Panorama: no displacement.
# Harmony of the Seas: Approximately 120,000 t (132,000 short tons)
# Allure of the Seas: Approximately 100,000 tons

# Let's check AIDAnova, Harmony of the Seas, Allure of the Seas, BRP Jose Rizal, RV Sikuliaq, Titan (submersible), A (sailing yacht - wait no mass for A).

# Also, what about submarines:
# KRI Nagapasa
# KRI Alugoro

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
        for k,v in data.items():
            if 'displacement' in k or 'weight' in k:
                if 'tons' in v or 'tonnes' in v or 'kg' in v or 'lb' in v or ' t ' in v or ' t' in v:
                    has_mass = True
            if 'height' in k or 'depth' in k:
                has_height = True

        if has_mass and has_height:
            print(f"\n--- {s} ---")
            for k in ['length', 'beam', 'draft', 'draught', 'depth', 'height', 'displacement', 'tonnage', 'weight', 'launched', 'commissioned', 'laid down', 'acquired', 'completed']:
                for dk, dv in data.items():
                    if k in dk:
                        print(f"{dk}: {dv}")
    except Exception:
        pass
    time.sleep(0.5)
