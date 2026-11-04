import urllib.request
import urllib.parse
import json

names = [
    "Navicula crassula",
    "Navicula siberica",
    "Coccomyces castanopsidis",
    "Coccomyces proteae"
]

for name in names:
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(name)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Name: {name}")
            print(f"  matchType: {data.get('matchType')}")
            print(f"  scientificName: {data.get('scientificName')}")
            print(f"  authorship: {data.get('authorship')}")
            print(f"  canonicalName: {data.get('canonicalName')}")
            print(f"  rank: {data.get('rank')}")
    except Exception as e:
        print(f"Error for {name}: {e}")
