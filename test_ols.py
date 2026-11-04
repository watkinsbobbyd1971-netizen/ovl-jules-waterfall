import urllib.request
import json
import gzip
import csv
import sys

with gzip.open('tasks/human_anatomy/chunk-0012.csv.gz', 'rt') as f:
    reader = csv.reader(f)
    next(reader)
    subjects = [row[1] for row in reader]

print("Total subjects:", len(subjects))
print("Sample subjects:", subjects[10:30])

# query EBI OLS for one
import urllib.parse
term = "Femur"
url = f"https://www.ebi.ac.uk/ols4/api/search?q={urllib.parse.quote(term)}&exact=true&ontology=uberon,fma"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())
    print("OLS response for Femur:", json.dumps(data['response']['docs'][:1], indent=2))
except Exception as e:
    print("Error:", e)
