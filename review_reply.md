Rule 9: "Empty beats a guess. No estimates, averages, typical values, values for a similar thing, or placeholders such as `unknown`. A subject with nothing sourced simply has no rows."

I programmatically searched both GBIF and Wikidata for these 1000 plant subjects.
- For GBIF, I checked the exact match species details for `isTerrestrial`, `isMarine`, `isFreshwater` and `habitats` (which yielded nothing). I also checked the occurrences endpoint for `lifeStage`, which yielded one placeholder string that the validator rejected.
- For Wikidata, I ran SPARQL queries checking for structural parts (P527) and habitats (P2974) and life stages (P3828), which returned absolutely no data.

Since no real verifiable measurements or structural details could be found for these subjects without hallucinating or guessing, the empty dataset is the correct output per the CORPUS-RULES.md guidelines.
