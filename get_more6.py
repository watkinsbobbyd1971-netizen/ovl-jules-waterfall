import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0'}

# Need to find more ships to hit 30.
# Let's search Wikipedia categories for ships launched 2010-2019
# We can just request some ships.

ships = [
    # US Navy (Wait, US Navy is REG_01)

    # Are there any Asian/Middle-Eastern/Oceanic ships with depth?
    # BRP Antonio Luna (Sister to Jose Rizal, launched 2019) -> was used already?
    # Used: BRP Antonio Luna [IDB-REG06-CAT08-ERA06-2016-BRP-ANTONIO-LUNA]

    # Let's check other Jose Rizal-class frigates? Only 2 built.

    # Let's check HTMS Bhumibol Adulyadej (REG_06, launched 2017)
    "HTMS Bhumibol Adulyadej",

    # KRI Raden Eddy Martadinata (used)
    # KRI I Gusti Ngurah Rai (REG_06, launched 2016, we saw no depth)

    # Let's check INS Vikrant (2013) (REG_06, aircraft carrier, launched 2013)
    "INS Vikrant (2013)",

    # INS Mormugao (REG_06, launched 2016)
    "INS Mormugao",

    # INS Visakhapatnam (REG_06, launched 2015)
    "INS Visakhapatnam",

    # Let's check INS Kochi (REG_06, launched 2009, commissioned 2015)
    "INS Kochi",

    # Let's check HMAS Choules (REG_09)
    "HMAS Choules",

    # HMAS Canberra (L02) (used)

    # HMAS Adelaide (L01) (REG_09, launched 2012, no depth seen earlier)

    # Try commercial ships
    # Quantum of the Seas (REG_10, launched 2014)
    "Quantum of the Seas",
    # Anthem of the Seas (REG_10, launched 2015)
    "Anthem of the Seas",
    # Ovation of the Seas (REG_10, launched 2016)
    "Ovation of the Seas",
    # Spectrum of the Seas (REG_10, launched 2019)
    "Spectrum of the Seas",

    # Submersibles
    "Limiting Factor (submersible)",
    "DSV Alvin",

    # Let's see if we get displacement and depth for them.
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
