import urllib.request
import urllib.parse
import json

# Let's try downloading the index
url = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/index.txt"
req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        lines = content.split('\n')
        print(f"Total lines: {len(lines)}")
        print("First 10 lines:")
        print('\n'.join(lines[:10]))
except Exception as e:
    print(e)
