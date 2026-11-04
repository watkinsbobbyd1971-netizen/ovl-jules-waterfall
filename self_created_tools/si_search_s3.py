import urllib.request
import urllib.parse
import json
import gzip
import csv
import sys
import time

def find_in_s3():
    # To find which unit is LIBSRC, let's look at the index
    url = "https://smithsonian-open-access.s3-us-west-2.amazonaws.com/metadata/edan/index.txt"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        indexes = [line.strip() for line in content.split('\n') if line.strip()]

    print(f"Total indexes: {len(indexes)}")
    # Can we find LIBSRC? Wait, maybe it's nmnhanthropology or something.
    for idx_url in indexes:
        if "lib" in idx_url.lower():
            print(f"Potential lib: {idx_url}")

    # Or just loop all index files... wait that's a lot. Let's print out all indexes.
    for idx_url in indexes:
        print(idx_url)

find_in_s3()
