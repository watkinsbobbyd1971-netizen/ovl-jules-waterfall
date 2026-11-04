import urllib.request
import urllib.parse
import json
import re

def search_ols(term):
    # Strip some modifiers like "Scorpaenichthys marmoratus vertebra" -> "vertebra"
    term = re.sub(r'^[A-Z][a-z]+ [a-z]+ ', '', term)
    term = term.lower().strip()
    term_quote = urllib.parse.quote(term)
    url = f"https://www.ebi.ac.uk/ols4/api/search?q={term_quote}&exact=true&ontology=uberon,fma"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read())
        docs = data.get('response', {}).get('docs', [])
        if docs:
            iri = docs[0].get('iri')
            label = docs[0].get('label')
            return iri, label, url
    except:
        pass
    return None, None, None

terms = ['Bone', 'mandible', 'vertebra', 'Bead', 'Scorpaenichthys marmoratus vertebra']
for t in terms:
    iri, label, url = search_ols(t)
    print(f"Term: {t} -> Label: {label}, IRI: {iri}")
