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
    url = f"https://api.catalogueoflife.org/nameusage/search?q={urllib.parse.quote(name)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data['result']:
                first = data['result'][0]
                usage = first.get('usage', {})
                name_info = usage.get('name', {})
                print(f"Name: {name}")
                print(f"  scientificName: {name_info.get('scientificName')}")
                print(f"  authorship: {name_info.get('authorship')}")
    except Exception as e:
        print(f"Error for {name}: {e}")
