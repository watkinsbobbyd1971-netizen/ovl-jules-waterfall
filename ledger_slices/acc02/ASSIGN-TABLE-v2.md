# ASSIGN-TABLE v2: acc02 research assignments (non-Jules workers)

Claimed 2026-11-03T15:20:41Z by claude-code-mac-studio (BigQuery job coord002_assign_v2_claim_20261103T152030Z). fill_ledger.assigned_worker is now agy for batches 002-011 and vm-codex for batches 012-021, 1,000 keys each.
Jules sessions could not run these batches: the account hit its daily limit (400 FAILED_PRECONDITION).

## Override of the TASK files
The TASK-acc02-batch-NNN-jules-<session>.md files apply unchanged: same research rules, same fact format, research only.
Only the output path changes. Write facts to output/facts/acc02/<worker>-batch_NNN.jsonl and the summary to output/facts/acc02/<worker>-batch_NNN-summary.md, on a branch of this repo.

| worker | batch | manifest | output |
|---|---|---|---|
| agy | 002 | ledger_slices/acc02/acc02_batch_002_jules-10274141118200915599.csv | output/facts/acc02/agy-batch_002.jsonl |
| agy | 003 | ledger_slices/acc02/acc02_batch_003_jules-10815999474767519177.csv | output/facts/acc02/agy-batch_003.jsonl |
| agy | 004 | ledger_slices/acc02/acc02_batch_004_jules-11340410582312011190.csv | output/facts/acc02/agy-batch_004.jsonl |
| agy | 005 | ledger_slices/acc02/acc02_batch_005_jules-11341207145988416842.csv | output/facts/acc02/agy-batch_005.jsonl |
| agy | 006 | ledger_slices/acc02/acc02_batch_006_jules-1138768997239189254.csv | output/facts/acc02/agy-batch_006.jsonl |
| agy | 007 | ledger_slices/acc02/acc02_batch_007_jules-11460984863184486419.csv | output/facts/acc02/agy-batch_007.jsonl |
| agy | 008 | ledger_slices/acc02/acc02_batch_008_jules-11776217541142937478.csv | output/facts/acc02/agy-batch_008.jsonl |
| agy | 009 | ledger_slices/acc02/acc02_batch_009_jules-1219466549110971038.csv | output/facts/acc02/agy-batch_009.jsonl |
| agy | 010 | ledger_slices/acc02/acc02_batch_010_jules-12976717753041984957.csv | output/facts/acc02/agy-batch_010.jsonl |
| agy | 011 | ledger_slices/acc02/acc02_batch_011_jules-14330237360221711114.csv | output/facts/acc02/agy-batch_011.jsonl |
| vm-codex | 012 | ledger_slices/acc02/acc02_batch_012_jules-14485360575888997082.csv | output/facts/acc02/vm-codex-batch_012.jsonl |
| vm-codex | 013 | ledger_slices/acc02/acc02_batch_013_jules-14505296534234109361.csv | output/facts/acc02/vm-codex-batch_013.jsonl |
| vm-codex | 014 | ledger_slices/acc02/acc02_batch_014_jules-14977114741073053556.csv | output/facts/acc02/vm-codex-batch_014.jsonl |
| vm-codex | 015 | ledger_slices/acc02/acc02_batch_015_jules-15028457964726757064.csv | output/facts/acc02/vm-codex-batch_015.jsonl |
| vm-codex | 016 | ledger_slices/acc02/acc02_batch_016_jules-15385677430484428025.csv | output/facts/acc02/vm-codex-batch_016.jsonl |
| vm-codex | 017 | ledger_slices/acc02/acc02_batch_017_jules-15424576435911611438.csv | output/facts/acc02/vm-codex-batch_017.jsonl |
| vm-codex | 018 | ledger_slices/acc02/acc02_batch_018_jules-15787508211503165881.csv | output/facts/acc02/vm-codex-batch_018.jsonl |
| vm-codex | 019 | ledger_slices/acc02/acc02_batch_019_jules-16387579049705877759.csv | output/facts/acc02/vm-codex-batch_019.jsonl |
| vm-codex | 020 | ledger_slices/acc02/acc02_batch_020_jules-1659231863374939202.csv | output/facts/acc02/vm-codex-batch_020.jsonl |
| vm-codex | 021 | ledger_slices/acc02/acc02_batch_021_jules-17630918581046126614.csv | output/facts/acc02/vm-codex-batch_021.jsonl |

On hold for Gemini, or for Jules once capacity returns: batch 001 and batches 022-043 (their keys stay unowned as 'misc' in fill_ledger until claimed).
