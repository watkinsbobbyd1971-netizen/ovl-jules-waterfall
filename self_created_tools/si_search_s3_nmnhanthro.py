import urllib.request
import json

url = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/nmnhanthro/00.txt"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    for i, line in enumerate(response):
        if i >= 5:
            break
        print(line.decode('utf-8')[:300])
