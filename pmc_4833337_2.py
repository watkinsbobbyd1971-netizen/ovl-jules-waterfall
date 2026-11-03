import urllib.request
import xml.etree.ElementTree as ET
import re

def fetch_pmc_full_text(pmc_id):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = f"?db=pmc&id={pmc_id}&retmode=xml"
    req = urllib.request.Request(base_url + params)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return ""

xml_str = fetch_pmc_full_text('4833337')
root = ET.fromstring(xml_str)
texts = ["".join(p.itertext()) for p in root.findall('.//body//p')]
for text in texts:
    text_lower = text.lower()
    if 'width' in text_lower or 'height' in text_lower or 'depth' in text_lower:
        print(text[:250])
