import urllib.request
import json
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://karmaka.de/?p=40548'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    res = urllib.request.urlopen(req, context=ctx).read().decode('utf-8')
    matches = re.finditer(r'.{0,100}(dimension|width|length|height|size|mass|weigh|gram|mm|cm|meter|inches|diameter).{0,100}', res, re.IGNORECASE)
    for m in matches:
        print(m.group(0))
except Exception as e:
    pass
