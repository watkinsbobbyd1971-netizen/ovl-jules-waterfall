#!/usr/bin/env python3
"""
Muse Overnight Multi-Hop & 6-Account Max Orchestrator (Jules + Vertex + Antigravity + Gemini Tasks).
Coordinates non-overlapping partitions ACC_01..ACC_06 across CAT_01..CAT_20 and REG_01..REG_10.
"""
ACCOUNTS = [
    {"slot": "ACC_01", "cats": ["CAT_01", "CAT_02", "CAT_03"], "libs": "LIB34..LIB38", "jules_vms": 60, "jules_tasks": 300},
    {"slot": "ACC_02", "cats": ["CAT_04", "CAT_05", "CAT_06"], "libs": "LIB39..LIB43", "jules_vms": 60, "jules_tasks": 300},
    {"slot": "ACC_03", "cats": ["CAT_07", "CAT_08", "CAT_09", "CAT_10"], "libs": "LIB44..LIB48", "jules_vms": 60, "jules_tasks": 300},
    {"slot": "ACC_04", "cats": ["CAT_11", "CAT_12", "CAT_13", "CAT_14"], "libs": "LIB49..LIB53", "jules_vms": 60, "jules_tasks": 300},
    {"slot": "ACC_05", "cats": ["CAT_15", "CAT_16", "CAT_17"], "libs": "LIB54..LIB58", "jules_vms": 60, "jules_tasks": 300},
    {"slot": "ACC_06", "cats": ["CAT_18", "CAT_19", "CAT_20"], "libs": "LIB59..LIB63", "jules_vms": 60, "jules_tasks": 300},
]
BIGQUERY_DISPATCH_TABLE = "ovl-machine-2026.image_corpus.waterfall_dispatch"
BIGQUERY_BLOCKS_TABLE = "ovl-machine-2026.image_corpus.blocks"
SCOREBOARD_DOC_ID = "1tI9RXKg0v4kOZwmSrxtPNAbrO35yu6CeQb9uC65TKNQ"
MUSE_PROMPTS_DOC_FOLDER_ID = "1ei-VtkIjeUA-4Zon2MqOfnKi0LvjDr1N"

if __name__ == "__main__":
    print(f"Loaded {len(ACCOUNTS)} account partitions (360 Jules VMs, 1,800 tasks/day) -> {BIGQUERY_BLOCKS_TABLE}")
