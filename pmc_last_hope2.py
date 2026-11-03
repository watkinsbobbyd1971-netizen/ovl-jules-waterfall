import urllib.request
import urllib.parse
import json
import re
import time

def check_wikipedia(title):
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={urllib.parse.quote(title)}&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        pages = data['query']['pages']
        for page_id, page_info in pages.items():
            if 'extract' in page_info:
                text = page_info['extract']
                l = re.findall(r'.{0,40}(?:length|long).{0,40}', text, re.IGNORECASE)
                h = re.findall(r'.{0,40}(?:height|tall|shoulder).{0,40}', text, re.IGNORECASE)
                m = re.findall(r'.{0,40}(?:weight|weigh|mass).{0,40}', text, re.IGNORECASE)

                has_l = [x for x in l if re.search(r'\d', x)]
                has_h = [x for x in h if re.search(r'\d', x)]
                has_m = [x for x in m if re.search(r'\d', x)]

                if has_l and has_h and has_m:
                    print(f"\nSpecies: {title}")
                    print("L:", has_l[:1])
                    print("H:", has_h[:1])
                    print("M:", has_m[:1])
    except Exception:
        pass

for t in ["Gaur", "Water buffalo", "Banteng", "Yak", "Takin", "Serow", "Goral", "Nilgai", "Blackbuck", "Indian rhinoceros", "Javan rhinoceros", "Sumatran rhinoceros"]:
    check_wikipedia(t)
    time.sleep(1)
