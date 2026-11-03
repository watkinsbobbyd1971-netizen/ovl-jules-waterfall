import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0'}

# Wait, if DWT or GT are not displacement, how many ships actually list displacement/mass AND height/depth?
# We found:
# - INS Vikrant (2013)
# - BRP Jose Rizal
# - RV Sikuliaq
# - Titan (submersible)
# - Harmony of the Seas
# - Allure of the Seas (launched 2009, completed 2010 -> so year 2010 works)

# Let's check some other known classes.
# Submarines don't list height/depth usually (except test depth which doesn't count).
# How about aircraft carriers from 2010-2019?
# - HMS Queen Elizabeth (R08) (REG_03 - out of region)
# - HMS Prince of Wales (R09) (REG_03)
# - Shandong (17) (REG_05 - out of region)
# - Gerald R. Ford (REG_01 - out of region)

# Let's check HMAS Adelaide (L01) - used to see no depth, but let's recheck.
# What about Japanese carriers/destroyers? (REG_05)
# South Korean? (REG_05)
# Indonesian? KRI I Gusti Ngurah Rai - let's check its class (Martadinata-class).
# Middle East? ENS Anwar El Sadat (Mistral-class amphibious assault ship, REG_07).

ships = [
    "ENS Anwar El Sadat",
    "ENS Gamal Abdel Nasser",
    "Mistral-class amphibious assault ship",
    "HMAS Adelaide (L01)",
    "Canberra-class landing helicopter dock",
    "BNS Bangabandhu",
    "HTMS Krabi"
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
        for k in ['length', 'beam', 'draft', 'draught', 'depth', 'height', 'displacement', 'tonnage', 'weight', 'launched', 'commissioned', 'laid down', 'acquired', 'completed']:
            for dk, dv in data.items():
                if k in dk:
                    print(f"{dk}: {dv}")
    except Exception:
        pass
    time.sleep(0.5)
