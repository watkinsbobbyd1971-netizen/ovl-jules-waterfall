import requests

def search_gbif(query):
    url = f"https://api.gbif.org/v1/species/match?name={query}"
    response = requests.get(url).json()
    return response

print(search_gbif("Broken Ceramic Jar"))
