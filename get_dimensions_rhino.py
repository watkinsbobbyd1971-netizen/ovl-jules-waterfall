import urllib.request
import json
import urllib.parse
import re

url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={urllib.parse.quote('Sumatran rhinoceros')}&format=json"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
response = urllib.request.urlopen(req)
data = json.loads(response.read().decode('utf-8'))
pages = data['query']['pages']
for page_id, page_info in pages.items():
    text = page_info['extract']
    for match in re.findall(r'.{0,60}(?:length|width|wide|height|tall|weight|weigh|mass).{0,60}', text, re.IGNORECASE):
        if re.search(r'\d', match):
            print(match.strip().replace('\n', ' '))
