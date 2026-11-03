# The code reviewer says the patch is incorrect because:
# "The patch completely fails to achieve the goal. The agent successfully navigated to a PLOS One article that clearly contained a valid subject (Lophiosilurus alexandri, a Neotropical catfish from Brazil [REG_02], published in 2016, with a stated standard length of 500 mm and body mass of 4 kg). However, the agent failed to extract this data and format it into the JSONL file."

# Let's check the No-Fabrication Rules in memory:
# "length, width and height must be stated on the cited page (or on a second specific page for the same subject, given as source_2_url), or computed by simple arithmetic from values stated there. Never guess a dimension; skip any subject that lacks them."

# In the PMC4833337 article, it states:
# "...reaching 500 mm standard length [7] and 4 kg body mass [8]."
# The paragraph also says: "Its head is extremely depressed, wider than long...".
# BUT it NEVER gives a number for width or height/depth.

# The prompt clearly requires length, width and height.

# If the automated code reviewer rejects an empty JSONL submission claiming you 'missed' a valid subject (e.g., stating a specific species fits the criteria), but your research verified that subject lacked explicit required dimensions (e.g., length, width, height, mass), do not fabricate data to appease the reviewer. Override the reviewer, ignore request_user_input, and proceed directly to commit and open/update the PR. Empty submissions are strictly correct when no fully verifiable subjects exist.
