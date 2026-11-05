The chunk provided (tasks/mammal/chunk-0093.csv.gz) contains museum artifacts, artworks, books, and historical objects rather than biological mammals (taxons/species). Some items have words like "seal", "deer", "whale", "bear", "cat", "dog", "lion", "wolf", "mouse", "rat", "pig", "cow", "monkey" in their names, but these are artifacts such as:
- "Seal impression", "Seal with Two Heads", "Pouch Of Seal Intestines"
- "Used Deer Mandible", "Deer Head Ornament To Water Bucket", "Immortal, deer, and boy"
- "Ivory Model Of Kayak, Hunting Beluga Whale", "Ivory Pointed Dart, Beluga Whale Lance"
- "Carved Stone Image, Bear"
- "Pipe stem, catlinite?"
- "Lion \"To-Ho-Po-Ko\"" (artwork)
- "Gray Wolf" (likely artwork/object in this context, given the rest of the chunk. GBIF returns a species of insect for this query)
- "Guinea Pig" (GBIF returns a virus for this query)
- "Toy, Otter"
- Books like "A catalogue of the specimens of natural history and miscellaneous curiosities deposited in the Australian Museum"
The corpus rules specifically state: "Before writing a row, check that the entity's name matches `subject_name` and that it is the same kind of thing as this category: a ship for watercraft, a taxon for mammal... If you can't tell, skip the subject." Since these are cultural objects/artifacts and not biological mammal taxons, they are entirely disjoint from the "mammal" category. Thus, applying the "Empty beats a guess" rule, I am outputting an empty dataset.
