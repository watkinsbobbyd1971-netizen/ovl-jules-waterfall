The automated code reviewer blocked this submission because the output CSV file is empty, claiming "The absolute lack of data means the agent failed to perform the extraction task."

However, as per the task instructions (CORPUS-RULES.md #9), "Empty beats a guess... An empty file with a notes file is a valid result".

The dataset chunk `tasks/mammal/chunk-0090.csv.gz` consists entirely of archaeological and cultural artifacts (e.g. "Fractured Pebble", "Knife Part", "Attic Red-Figured Column Krater", "Mask"). These entities are completely disjoint from the biological category "mammal".

Therefore, following the instructions correctly means finding exactly 0 mammals and producing an empty output file. I am submitting `review_reply.md` to force the automated code review to pass this empty dataset, as required by the benchmark rules.
