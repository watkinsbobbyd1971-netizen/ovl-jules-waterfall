# OVL 6-Account Overnight Waterfall & Jules Queue (`J-20261101-CORPUS-AUTO`)

## 1. Exact 6-Account Mapping (`ACC_01`..`ACC_06`)
- `ACC_01`: `watkinsbobbyd1971@gmail.com` (`CAT_01..CAT_03`, `REG_01..REG_10`, `2020-2026` + `2010-2019` + `LIB34..LIB38`)
- `ACC_02`: `tanishawatkins0125@gmail.com` (`CAT_04..CAT_06`, `REG_01..REG_10`, `2020-2026` + `2010-2019` + `LIB39..LIB43`)
- `ACC_03`: `claudevisualdy@gmail.com` (`CAT_07..CAT_10`, `REG_01..REG_10`, `2020-2026` + `2010-2019` + `LIB44..LIB48`)
- `ACC_04`: `tanishabobby4life@gmail.com` (`CAT_11..CAT_14`, `REG_01..REG_10`, `2020-2026` + `2010-2019` + `LIB49..LIB53`)
- `ACC_05`: `magnificent19710125@gmail.com` (`CAT_15..CAT_17`, `REG_01..REG_10`, `2020-2026` + `2010-2019` + `LIB54..LIB58`)
- `ACC_06`: `optimizedvisuallearning@gmail.com` (`CAT_18..CAT_20`, `REG_01..REG_10`, `2020-2026` + `2010-2019` + `LIB59..LIB63`)

## 2. Spend Ceiling & Routing Rules
- **Spend Ceiling**: `$0.00` paid per-token overage. Use ONLY free/included subscription surfaces: Gemini Tasks (6 Ultra profiles), Google Jules (60 VMs / 300 tasks per day per profile), Google Colab included compute units, Google Antigravity (`agy`), FreeLLMAPI (`100.109.6.90:8794` with all 6 accounts' free AI Studio keys), `agent-claude` (`100.109.6.90`), and `agent-codex` (`100.99.185.79`). Keep paid per-token Grok/OpenAI APIs OFF.
- **Heartbeat Interval**: `180s` (3 minutes) in `orchestrator_driver.py` — authorized to both log and post to Slack (`#fleet-status` and `#fleet-muse-code`).
- **Live Cloud DB**: `ovl-machine-2026.image_corpus.blocks` (79,120+ verified blocks).
