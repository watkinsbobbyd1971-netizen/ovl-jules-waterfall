import urllib.request
import urllib.parse
import json

def search_met(query):
    url = f"https://collectionapi.metmuseum.org/public/collection/v1.1/search?q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('objectIDs'):
                obj_id = data['objectIDs'][0]
                obj_url = f"https://collectionapi.metmuseum.org/public/collection/v1.1/objects/{obj_id}"
                req2 = urllib.request.Request(obj_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req2) as resp2:
                    obj_data = json.loads(resp2.read().decode())
                    return obj_data
    except Exception as e:
        print(f"Error {e}")
    return None

print(search_met("Evelyn Nesbit"))
