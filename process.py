import os

os.makedirs('out/plant', exist_ok=True)

with open('out/plant/chunk-0024.csv', 'w') as f:
    f.write('canonical_dedup_key,column_name,value,source_url\n')

with open('out/plant/chunk-0024.notes.txt', 'w') as f:
    f.write('The subjects in this chunk (e.g., "Bottle", "Mellin\'s Food for Infants and Invalids", "Winnowing basket", "Pestle", "Pitcher") were verified against Wikidata and GBIF to be artifacts or tools rather than biological plants. They do not match the expected biological scope (kingdom="Plantae"). No botanical data could be extracted. Outputting an empty dataset.\n')
