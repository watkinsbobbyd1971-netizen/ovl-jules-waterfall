import requests
import json
import re
import urllib.parse
from bs4 import BeautifulSoup
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
}

ships_list = [
    "KRI Nagapasa",
    "KRI Alugoro",
    "BRP Jose Rizal",
    "KRI Tarakan (905)",
    "KRI Bima Suci",
    "UMS Minye Theinkhathu",
    "BNS Shadhinota",
    "BNS Prottoy",
    "HTMS Krabi",
    "HTMS Prachuap Khiri Khan",
    "KRI I Gusti Ngurah Rai",
    "ENS Tahya Misr",
    "ENS Anwar El Sadat",
    "ENS Gamal Abdel Nasser",
    "INS Rahav",
    "INS Tanin (2012)",
    "BNS Bangabandhu",
    "ENS El Fateh",
    "NNS Centenary",
    "NNS Unity",
    "NNS Karaduwa",
    "CGS Barracuda",
    "HMAS Adelaide (L01)",
    "HMAS Hobart (DDG 39)",
    "HMAS Brisbane (DDG 41)",
    "HMAS Sydney (DDG 42)",
    "HMNZS Aotearoa",
    "HMNZS Wellington (P55)",
    "RV Kronprins Haakon",
    "RRS Sir David Attenborough",
    "RSV Nuyina",
    "RV Sikuliaq"
]

for ship in ships_list:
    url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(ship)}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"{ship}: HTTP {resp.status_code}")
            continue
        soup = BeautifulSoup(resp.text, 'html.parser')
        infobox = soup.find('table', class_='infobox')
        if not infobox:
            print(f"{ship}: No infobox")
            continue

        data = {}
        for tr in infobox.find_all('tr'):
            th = tr.find('th')
            td = tr.find('td')
            if th and td:
                label = th.get_text(strip=True).lower()
                val = td.get_text(separator=' ', strip=True)
                data[label] = val

        print(f"\n--- {ship} ---")
        for k in ['length', 'beam', 'draft', 'draught', 'depth', 'height', 'displacement', 'tonnage', 'weight', 'launched', 'commissioned', 'laid down', 'acquired', 'completed']:
            for dk, dv in data.items():
                if k in dk:
                    print(f"{dk}: {dv}")

    except Exception as e:
        print(f"{ship}: {e}")
    time.sleep(0.5)
