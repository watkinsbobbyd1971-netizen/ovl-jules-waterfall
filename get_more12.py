import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0'}

ships = [
    "Harmony of the Seas",
    "Allure of the Seas",
    "Titan (submersible)",
    "RV Sikuliaq",
    "BRP Jose Rizal",
    "INS Vikrant (2013)"
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
