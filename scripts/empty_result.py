import csv

with open('out/human_anatomy/chunk-0013.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['canonical_dedup_key', 'column_name', 'value', 'source_url'])

with open('out/human_anatomy/chunk-0013.notes.txt', 'w') as f:
    f.write("Dataset chunk contains museum artifacts (prints, drawings, postcards, clothing, etc.), not human anatomical structures. Queried OLS (fma, uberon) for exact matches but all found matches (e.g., 'bar', 'rattle', 'drawing', 'print') were false positives corresponding to unrelated artifact definitions or non-human anatomy. Excluded to maintain strictly real, sourced values as per instructions.\n")
