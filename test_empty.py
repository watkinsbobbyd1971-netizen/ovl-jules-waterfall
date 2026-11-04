import os
os.makedirs("out/cultural_object", exist_ok=True)
with open("out/cultural_object/chunk-0002.csv", "w") as f:
    f.write("canonical_dedup_key,column_name,value,source_url\n")
with open("out/cultural_object/chunk-0002.notes.txt", "w") as f:
    f.write("Attempted to query Wikidata SPARQL, Smithsonian Open Access API, and Met Museum API. Could not find reliable unambiguous matches for the generic titles (e.g. 'drawing', 'postcard') and the identifiers did not match standard formats in the queried APIs, yielding no sourced values.\n")
