import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0'}

subs = [
    # subs usually list draft, which is not height, but test depth is. However, test depth is not bounding box depth.
    # Bounding box of a sub is length, beam (which is usually the diameter of the cylinder, so height = beam).
    # Can we say height = beam for submarines if not explicitly stated?
    # NO. The prompt says: "Never guess a dimension; skip any subject that lacks them." "All three dimensions (L/W/H) must be explicitly stated."

    # Are there any other ships with explicit height/depth?
    "Celebrity Edge",
    "MSC Meraviglia",
    "Genting Dream",
    "MSC Bellissima",
    "Costa Venezia",
    "Norwegian Joy",
    "Oasis of the Seas",
    "Anthem of the Seas",
    "Quantum of the Seas",
    "Ovation of the Seas",
    "AIDAprima",
    "AIDAperla",
    "Norwegian Escape",
    "Carnival Vista",
    "Carnival Horizon",
    "Majestic Princess",
    "Flying Fox (yacht)",
    "Black Pearl (yacht)"
]

for s in subs:
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
