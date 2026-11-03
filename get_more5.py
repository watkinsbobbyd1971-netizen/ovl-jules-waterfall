import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0'}

# Need ships from REG_06 to REG_10.
# REG_06: South & Southeast Asia
# REG_07: Middle East & North Africa
# REG_08: Sub-Saharan Africa
# REG_09: Oceania & Pacific
# REG_10: Polar, Oceanic & Orbital

ships = [
    # BRP Jose Rizal (REG_06, 2019, L, W, Depth, Mass) -> wait, was depth L/W/Depth/Mass all there?
    # Yes: length 107m, beam 13.8m, depth 6.9m, displacement 2600t, launched 2019.

    # RV Sikuliaq (REG_10 - oceanic research, 2012, L, W, Depth, Mass)
    # length 79.6m, beam 15.85m, depth 8.5m, displacement 3724 t, launched 2012.

    # Titan (submersible) (REG_10 - oceanic, 2018, L, W, H, Mass)
    # length 6.7m, beam 2.8m, height 2.5m, displacement 10432 kg, completed 2018.

    # Harmony of the Seas (REG_10, 2015/2016, L, W, Depth, Mass)
    # length 362.12m, beam 47.42m, depth 22.6m, displacement 120,000 t, launched 2015.

    # Allure of the Seas (REG_10, 2009/2010, L, W, Depth, H, Mass)
    # launched 2009 (not 2010s), completed 2010 (we can use 2010).
    # length 362m, beam 47m, depth 22.5m, displacement 100,000 tons.

    "BRP Jose Rizal",
    "RV Sikuliaq",
    "Titan (submersible)",
    "Harmony of the Seas",
    "Allure of the Seas"
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
