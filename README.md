# OVL Jules Cloud Waterfall Repository (Self-Contained / Zero-Question Mode)

All data files (`queue_batch_01.csv`) and the `v3.0.0` compiler (`jules_waterfall_worker.py`) are self-contained inside this repository on `main` and all 5 profile branches (`profile-1-cat01-04` through `profile-5-cat17-20`).

## Autonomous Execution (No External Credentials Required)
```bash
python3 jules_waterfall_worker.py
```
This reads `queue_batch_01.csv` from the repo root and writes the compiled `IMAGE_DATA_BLOCK v3.0.0` JSONL files into `output/`:
- `output/batch_01_v3.jsonl`
- `output/profile-1-batch.jsonl`
- `output/profile-2-batch.jsonl`
- `output/profile-3-batch.jsonl`
- `output/profile-4-batch.jsonl`
- `output/profile-5-batch.jsonl`
