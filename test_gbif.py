import urllib.request
import urllib.parse
import json

def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return json.loads(urllib.request.urlopen(req).read().decode())

def search_gbif(name):
    url = f"https://api.gbif.org/v1/species/match?name={urllib.parse.quote(name)}"
    resp = get_json(url)
    print(f"GBIF {name}:", resp.get('matchType'), resp.get('scientificName'), resp.get('authorship'))

def search_wikidata(name):
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(name)}&language=en&format=json"
    resp = get_json(url)
    if resp.get('search'):
        q = resp['search'][0]['id']
        print(f"WD {name}:", q)
        ent_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={q}&props=claims&format=json"
        ent = get_json(ent_url)['entities'][q]['claims']
        if 'P2067' in ent:
            print("  Mass:", ent['P2067'][0]['mainsnak']['datavalue']['value'])
        if 'P2060' in ent:
            print("  Wingspan:", ent['P2060'][0]['mainsnak']['datavalue']['value'])
        if 'P225' in ent:
            print("  Taxon name:", ent['P225'][0]['mainsnak']['datavalue']['value'])
    else:
        print(f"WD {name}: NOT FOUND")

search_gbif("Falco columbarius")
search_wikidata("Falco columbarius")
search_wikidata("Western Barn Owl")
search_wikidata("European Bee-eater")
search_gbif("Great cormorant")
