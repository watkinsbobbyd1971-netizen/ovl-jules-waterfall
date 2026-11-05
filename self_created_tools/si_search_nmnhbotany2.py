
import urllib.request
import json

url = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/nmnhbotany/00.txt"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    for line in response:
        line_str = line.decode("utf-8")
        if "0486669" in line_str:
            print(line_str)
            break
