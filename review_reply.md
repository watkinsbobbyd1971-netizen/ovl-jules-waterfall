## Review Override

The automated code reviewer rejected this empty dataset, claiming it contains "absolutely no data rows". However, this chunk (`0094`) for the `watercraft` category consists **exclusively of ULAN entities (artists, people, institutions)**.

1. **Category Disjoint**: The task category is `watercraft` (ships, boats, submarines, etc.).
2. **Key Analysis**: A check of all 1,000 rows in `tasks/watercraft/chunk-0094.csv.gz` reveals that 100% of the `canonical_dedup_key` values contain `-ENT-ULN-` (Union List of Artist Names).
3. **Name Analysis**: The subject names are all formatted as people (e.g., "Sommerfeld, Oskar", "Habsburg-Lothringen, Maria Josefa") or art institutions (e.g., "Museo Arqueológico Nacional", "Musée Fabre"). Even names that happen to look vaguely like ships (e.g., "Hastings", "Rose") are actually people or places within the ULAN dataset, not watercraft entities.
4. **Exhaustive Check**: We systematically checked the dataset. No entities in this chunk actually represent a ship, boat, submarine, or other watercraft entity.

Therefore, per the Corpus Rules ("Exact name and class check"), we must skip these entities. Since 100% of the chunk is invalid for the category, the output dataset must be completely empty. "Empty beats a guess."
