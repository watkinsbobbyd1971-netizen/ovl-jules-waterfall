import urllib.request
import urllib.parse
import json
import gzip
import csv
import concurrent.futures

def get_wikidata_anatomy(subject):
    # Query for items where English label is exactly the subject, and it is a subclass or instance of an anatomical structure (Q4936952 or Q17387346 etc)
    # However we just search Wikidata API for entity matches and check if it has P361 (part of), P31 (instance of) etc...
    # This might rate limit, let's just see.
    pass

if __name__ == "__main__":
    pass
