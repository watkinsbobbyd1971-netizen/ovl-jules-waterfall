import urllib.request
import json
import ssl
import re
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=hailstone%202022&utf8=&format=json',
    'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=hailstone%202023&utf8=&format=json',
    'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=hailstone%202024&utf8=&format=json',
    'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=hailstone%202025&utf8=&format=json',
    'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=hailstone%202026&utf8=&format=json',
]

for url in urls:
    print(f"Fetching {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        res = urllib.request.urlopen(req, context=ctx).read()
        print(json.loads(res)['query']['search'])
    except Exception as e:
        print(e)
    time.sleep(1)
