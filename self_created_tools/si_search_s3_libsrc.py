import urllib.request
import urllib.parse
import json
import gzip
import os

url = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/sil/index.txt"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    content = response.read().decode('utf-8')
    indexes = [line.strip() for line in content.split('\n') if line.strip()]

print(f"SIL index files: {len(indexes)}")
if indexes:
    print(f"First: {indexes[0]}")
    # Download first and check if our IDs are there
    req = urllib.request.Request(indexes[0])
    with urllib.request.urlopen(req) as response:
        with open("sil_test.txt", "wb") as f:
            f.write(response.read())
