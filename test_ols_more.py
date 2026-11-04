import urllib.request
import urllib.parse
import json

terms = ['Bone', 'mandible', 'vertebra', 'Bead', 'Scorpaenichthys marmoratus vertebra']
for term in terms:
    url = f"https://www.ebi.ac.uk/ols4/api/search?q={urllib.parse.quote(term)}&exact=true&ontology=uberon,fma"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        print(f"OLS response for {term}: {len(data['response']['docs'])} hits")
        if data['response']['docs']:
            print(f" First hit: {data['response']['docs'][0].get('label')} - {data['response']['docs'][0].get('ontology_name')}")
    except Exception as e:
        print("Error:", e)
