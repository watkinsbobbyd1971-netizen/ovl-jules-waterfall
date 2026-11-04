import urllib.request
import json
import urllib.parse

def test_gbif():
    url = "https://api.gbif.org/v1/species/match?name=Asteromella%20ixiolirii"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print(data)

        usage_key = data.get("usageKey")
        if usage_key:
            url_details = f"https://api.gbif.org/v1/species/{usage_key}"
            req_details = urllib.request.Request(url_details)
            with urllib.request.urlopen(req_details) as response_details:
                details = json.loads(response_details.read().decode())
                print(details.get("authorship"))

test_gbif()
