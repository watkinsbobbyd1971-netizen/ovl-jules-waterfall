import json
import csv
import gzip

with open('filtered_wd_map.json') as f:
    wd_map = json.load(f)

# The reviewer said rated_power should be P2791 (nominal power). P2102 is boiling point.
# Oh, my initial memory search gave:
# "For electronics corpus tasks, the Wikidata API is effective for querying properties such as component_relationship (P527), descriptive_identity (P31, P279), dimension_length (P2043), manufacturer_or_creator (P170, P176), mass (P2067), material_identity (P186), and rated_power (P2102)."
# Wait, memory said P2102. Is P2102 boiling point? Yes.
# So the memory was flawed, but I have to fix it to P2791.

prop_to_col = {
    'P527': 'component_relationship',
    'P31': 'descriptive_identity',
    'P279': 'descriptive_identity',
    'P2043': 'dimension_length',
    'P170': 'manufacturer_or_creator',
    'P176': 'manufacturer_or_creator',
    'P2067': 'mass',
    'P186': 'material_identity',
    'P2791': 'rated_power',
    'P2874': 'model_identifier'
}

print("Running query again with P2791 instead of P2102...")
