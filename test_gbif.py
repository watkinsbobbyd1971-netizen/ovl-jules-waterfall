import urllib.request
import json
import urllib.parse
import re
import csv
import gzip

def get_gbif_data(name):
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(name)}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(e)
        return None

print(get_gbif_data("Asteromella ixiolirii"))
