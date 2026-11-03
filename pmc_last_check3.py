import urllib.request
import re
import json

def get_wikipedia(title):
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={urllib.parse.quote(title)}&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        for page_id, page_info in data['query']['pages'].items():
            if 'extract' in page_info:
                text = page_info['extract']
                l = [x for x in re.findall(r'.{0,40}(?:length|long).{0,40}', text, re.IGNORECASE) if re.search(r'\d', x)]
                w = [x for x in re.findall(r'.{0,40}(?:width|wide|wingspan|span).{0,40}', text, re.IGNORECASE) if re.search(r'\d', x)]
                h = [x for x in re.findall(r'.{0,40}(?:height|tall|shoulder).{0,40}', text, re.IGNORECASE) if re.search(r'\d', x)]
                m = [x for x in re.findall(r'.{0,40}(?:weight|weigh|mass).{0,40}', text, re.IGNORECASE) if re.search(r'\d', x)]
                if l and w and h and m:
                    print(f"\nSpecies: {title}")
                    print("L:", l[:1])
                    print("W:", w[:1])
                    print("H:", h[:1])
                    print("M:", m[:1])
    except Exception:
        pass

for sp in ["Megalania", "Gharial", "Mugger crocodile", "Spectacled caiman", "Black caiman"]:
    get_wikipedia(sp)
