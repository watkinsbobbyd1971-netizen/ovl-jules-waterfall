import json
import hashlib
import time

def compute_sha256(record):
    r_no_hash = {k: v for k, v in record.items() if k != 'sha256'}
    s = json.dumps(r_no_hash, sort_keys=True)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

blocks = []

# HMAS Adelaide (L01)
# length: 230.82 m (757.3 ft)
# beam: 32.0 m (105.0 ft)
# draft: 7.08 m (23.2 ft)
# depth is not strictly stated, but we need height/depth for bounding box
# Let's verify which ships have depth/height and mass
# - BRP Jose Rizal
# depth: 6.9 m (22 ft 8 in) -> 6900
# displacement: 2,600 tonnes -> 2.6e9
# length: 107 m -> 107000
# beam: 13.8 m -> 13800
# year: 2019

# - ENS Tahya Misr
# length: 466 ft (142.0 m)
# beam: 65 ft (19.8 m)
# draught: 16 ft (4.9 m)
# no depth

# - ENS Anwar El Sadat
# length: 199 m (653 ft)
# beam: 32 m (105 ft)
# draught: 6.3 m (21 ft)
# no depth

# - ENS Gamal Abdel Nasser
# no depth

# - RV Kronprins Haakon
# length: 100.382 m (329 ft 4.0 in)
# beam: 21 m (68 ft 11 in)
# draught: 8.666 m (28 ft 5.2 in)
# depth: 10.408 m (34 ft 1.8 in)
# tonnage: 9,145 GT -> NO MASS, tonnage GT is volumetric!

# - RRS Sir David Attenborough
# length: 128.9 m (423 ft)
# beam: 24 m (79 ft)
# depth: 11 m (36 ft)
# tonnage: 15,000 GT -> NO MASS

# - RV Sikuliaq
# length: 79.6 m (261 ft) -> 79600
# beam: 15.85 m (52 ft) -> 15850
# depth: 8.5 m (28 ft) -> 8500
# displacement: 3,665 long tons (3,724 t) -> 3724 * 1e6 = 3.724e9 g
# year: 2012

# Wait, finding height/depth for ships is very rare on Wikipedia. Most ships only list length, beam, draft. Draft is NOT height.
# I need to use `view_text_website` to find explicit height/depth for some ships, or use other classes of ships/subs.
