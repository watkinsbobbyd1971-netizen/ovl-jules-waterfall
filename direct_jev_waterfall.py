#!/usr/bin/env python3
"""
Direct HTTP TypeSafe Jev v1.14.0 Client (Zero Composio/MCP Connector Calls)
Calls https://api.typesafe.ai/v1/systemone or http://100.109.6.90:8792/v1/systemone directly.
"""
import os, json, urllib.request

JEV_DIRECT_URL = "https://api.typesafe.ai/v1/systemone"
JEV_RELAY_URL = "http://100.109.6.90:8792/v1/systemone"
JEV_MODEL = "jev-1.14.0"

def classify_record_direct_jev(record_text: str) -> dict:
    payload = {
        "model": JEV_MODEL,
        "state": {"record": record_text},
        "questions": {
            "category_code": {"type": "choice", "choices": [f"CAT_{i:02d}" for i in range(1, 21)], "instructions": "Select the exact OVL category_code."},
            "region_code": {"type": "choice", "choices": [f"REG_{i:02d}" for i in range(1, 11)], "instructions": "Select the exact global region_code."},
            "era_code": {"type": "choice", "choices": [f"ERA_{i:02d}" for i in range(1, 9)], "instructions": "Select the historical/modern era_code."}
        }
    }
    env_val = os.environ.get("TYPESAFE_JEV_API_KEY", "").strip()
    url = JEV_DIRECT_URL if env_val else JEV_RELAY_URL
    headers = {"Content-Type": "application/json"}
    if env_val:
        headers["Authorization"] = f"Bearer {env_val}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        ans = data.get("answers", {})
        return {
            "category_code": ans.get("category_code", {}).get("choice", "CAT_17"),
            "region_code": ans.get("region_code", {}).get("choice", "REG_01"),
            "era_code": ans.get("era_code", {}).get("choice", "ERA_07")
        }
