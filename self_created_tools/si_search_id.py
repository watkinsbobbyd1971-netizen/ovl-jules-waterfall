import urllib.request
import urllib.parse
import json

def try_fetch(id_str):
    urls = [
        f"https://n2t.net/ark:/65665/kb6{id_str}",
        f"https://n2t.net/ark:/65665/{id_str}",
        f"https://ids.si.edu/ids/deliveryService?id={id_str}",
        f"https://collections.si.edu/search/results.htm?q={id_str}&format=json"
    ]
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                print(f"Success for {u}")
                print(response.read(100).decode('utf-8'))
        except Exception as e:
            print(f"Failed {u}: {e}")

try_fetch("0475223")
