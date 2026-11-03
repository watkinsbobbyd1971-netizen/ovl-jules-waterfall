import urllib.request
import urllib.parse
import json
import re

# I need to find specific animals for CAT12, 2020-2026, R06-10 with measurements.
# Let's search Wikipedia API for new species of lizard/gecko from these regions that were discovered 2020-2026.
# Or better yet, we can use the subjects we found in PMC articles previously, like Hylarana raniceps, but PMC didn't have width/height.
# Let's search Wikipedia for recent species.
# Search wiki for "length", "width", "weight" in species.

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
                # Search for all 3 dimensions and mass

                # Check for length
                l = re.findall(r'.{0,40}(?:length|long).{0,40}', text, re.IGNORECASE)
                w = re.findall(r'.{0,40}(?:width|wide|span).{0,40}', text, re.IGNORECASE)
                h = re.findall(r'.{0,40}(?:height|tall|shoulder).{0,40}', text, re.IGNORECASE)
                m = re.findall(r'.{0,40}(?:weight|weigh|mass).{0,40}', text, re.IGNORECASE)

                has_l = [x for x in l if re.search(r'\d', x)]
                has_w = [x for x in w if re.search(r'\d', x)]
                has_h = [x for x in h if re.search(r'\d', x)]
                has_m = [x for x in m if re.search(r'\d', x)]

                if has_l and has_w and has_h and has_m:
                    print(f"\nSpecies: {title}")
                    print("L:", has_l[:1])
                    print("W:", has_w[:1])
                    print("H:", has_h[:1])
                    print("M:", has_m[:1])
    except Exception:
        pass

for t in ["Cane toad", "Goliath frog", "African bullfrog", "Marine iguana", "Komodo dragon"]:
    check_wikipedia(t)
