import urllib.request
import re
import xml.etree.ElementTree as ET
import time

ids = ['13685806', '13645082', '11684376']
for uid in ids:
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={uid}&retmode=xml"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req)
        content = response.read().decode('utf-8')
        root = ET.fromstring(content)
        texts = [elem.text for elem in root.iter() if elem.text]
        full_text = " ".join(texts)
        matches = re.findall(r'.{0,40}(?:weight|mass|g |body length|width|tall|height|mm |cm |kg ).{0,40}', full_text, re.IGNORECASE)
        valid = [m.strip().replace('\n', ' ') for m in matches if re.search(r'\d', m)]
        print(f"\n--- PMC{uid} ---")
        for m in list(set(valid))[:10]:
            print(m)
    except Exception:
        pass
    time.sleep(1)
