import urllib.request
import urllib.parse
import json
import gzip
import csv

# Can we find these using exact property match in Wikidata?
# Wait, "LIBSRC-LIB51-ENT-SMI-0475223". What is the SMI id?
# Maybe it's a Smithsonian id? Let's check some records from 'sil_test.txt'.
# The ids in sil_test.txt are "ld1-...", but there is a "record_ID":"siris_sil_666319".
# "0475223" - 7 digits. Could it be siris_sil_475223? Or siris_arc_...? Or nmnh_...?

# Let's search a few terms from the CSV
pass
