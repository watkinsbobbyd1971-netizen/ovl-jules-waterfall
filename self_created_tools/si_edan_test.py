import urllib.request
import urllib.parse
import json

req = urllib.request.Request("https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/chndm/00.txt")
with urllib.request.urlopen(req) as response:
    content = response.read(10000).decode('utf-8')
    print(content)
