1. **Explore the workspace & research**
   - I have explicitly viewed the Wikipedia pages for Harmony of the Seas, Allure of the Seas, BRP Jose Rizal, RV Sikuliaq, Titan (submersible), and INS Vikrant (2013) to meet the reviewer's requirement for viewing text websites explicitly.
2. **Generate the JSONL output**
   - I wrote a python script `create_jsonl.py` which populated 6 blocks with accurate information taken directly from Wikipedia pages. I have skipped other ships since they lack at least one explicitly stated required bounding box dimension (usually height/depth).
   - I will use `run_in_bash_session` to re-run `create_jsonl.py` to ensure the output is generated properly.
3. **Verify the generated JSONL**
   - Use `cat` and `validate_jules_batch.py` to ensure the output meets all criteria.
4. **Stage and Commit the file**
   - `git add output/profile-ACC_03/batch_04_CAT08_2010S_R06-10_v3.jsonl`
   - `git commit -m "Add batch 04 records for CAT08"`
5. **Generate the pull request description**
   - Create a text file containing the total count (N=6) and one line per block with the format: `canonical_dedup_key | verification_citation_url`.
6. **Complete pre-commit steps**
   - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
7. **Submit the PR**
   - Use `gh pr create --title "[ACC_03] batch_04 CAT08_2010S_R06-10 (6 verified blocks)" --body-file pr_desc.txt`
   - Use the `submit` tool to finish the task.
