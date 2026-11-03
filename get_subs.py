import requests
import urllib.parse
from bs4 import BeautifulSoup
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
}

subs = [
    # Submarines usually have a cylindrical hull where beam/width = height, or height is explicitly listed
    # Wait, subs also often just list length and beam.
    # Let's check some sub classes
    "Scorpène-class submarine",
    "Type 209 submarine",
    "Type 214 submarine",
    "Collins-class submarine",
    "Soryu-class submarine",
    "Taigei-class submarine"
]

for sub in subs:
    url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(sub)}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"{sub}: HTTP {resp.status_code}")
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

        print(f"\n--- {sub} ---")
        for k in ['length', 'beam', 'draft', 'draught', 'depth', 'height', 'displacement', 'tonnage', 'weight', 'hull']:
            for dk, dv in data.items():
                if k in dk:
                    print(f"{dk}: {dv}")

    except Exception as e:
        pass
    time.sleep(1)
