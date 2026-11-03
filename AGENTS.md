# AGENTS.md — Google Jules Autonomous Execution Rules (ZERO QUESTIONS)

## CRITICAL RULE FOR GOOGLE JULES
1. **NEVER ask the user clarifying questions.** All inputs, schemas, and data files are already inside this repository.
2. **NEVER attempt to connect to Google Drive, BigQuery, or external APIs.** Work strictly on the local files committed in this repository.
3. **Default Autonomous Action:**
   - Read `queue_batch_01.csv` in the repository root.
   - Run `python3 jules_waterfall_worker.py`.
   - Verify that `output/batch_01_v3.jsonl` and `output/profile-1-batch.jsonl` through `output/profile-5-batch.jsonl` are generated and non-empty.
   - Commit the generated files in `output/` directly to the current branch and open/update the Pull Request immediately without asking any questions.
