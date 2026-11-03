# AGENTS.md — ZERO-QUESTION AUTONOMOUS EXECUTION MANDATE
1. NEVER ask clarifying questions.
2. NEVER make external network or Google Drive calls.
3. Read local `batches/batch_*.csv` or `queue_batch_01.csv` and execute `python3 jules_waterfall_worker.py` immediately.
4. Commit all generated `output/*.jsonl` files directly to this branch.
