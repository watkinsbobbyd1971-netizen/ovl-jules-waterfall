#!/usr/bin/env bash
# ==============================================================================
# OVL JULES 6-PROFILE ACCOUNT-AWARE SPAWNER
# Bounded, observable, dry-run by default across reconciled canonical accounts
# ==============================================================================
set -euo pipefail

REPO="watkinsbobbyd1971-netizen/ovl-jules-waterfall"
LIVE_FLAG=()
if [ "${1:-}" = "--live" ]; then
  LIVE_FLAG=("--live")
fi

# Canonical branch to account mappings
BRANCH_SPECS=(
  "profile-1-cat01-04:ACC_01:watkinsbobbyd1971@gmail.com:1"
  "profile-2-cat05-08:ACC_02:tanishawatkins0125@gmail.com:2"
  "profile-3-cat09-12:ACC_03:claudevisualdy@gmail.com:3"
  "profile-4-cat13-16:ACC_04:tanishabobby4life@gmail.com:4"
  "profile-5-cat17-20:ACC_05:magnificent19710125@gmail.com:5"
  "profile-6-global-all20:ACC_06:optimizedvisuallearning@gmail.com:6"
)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISPATCHER="${SCRIPT_DIR}/ovl_jules_dispatch.py"

echo "Evaluating parallel Jules cloud VM sessions across reconciled accounts (Dry-run default)..."

FAILED=0
DISPATCHED=0

for SPEC in "${BRANCH_SPECS[@]}"; do
  IFS=':' read -r BRANCH ACC_ID EMAIL PROFILE_N <<< "$SPEC"
  for BATCH in $(seq -w 1 10); do
    PROMPT="On branch ${BRANCH}, read AGENTS.md and run python3 jules_waterfall_worker.py ${BATCH} locally with zero external network calls or questions, and commit ONLY output/profile-${PROFILE_N}/batch_${BATCH}_v3.jsonl directly to ${BRANCH}; never modify shared root files."
    MANIFEST_CLAIM="batch_${BATCH}_${BRANCH}_${ACC_ID}"

    if python3 "${DISPATCHER}" \
      --repo "${REPO}" \
      --branch "${BRANCH}" \
      --acc-id "${ACC_ID}" \
      --email "${EMAIL}" \
      --profile-n "${PROFILE_N}" \
      --manifest "${MANIFEST_CLAIM}" \
      --prompt "${PROMPT}" \
      ${LIVE_FLAG[@]+"${LIVE_FLAG[@]}"}; then
      DISPATCHED=$((DISPATCHED + 1))
    else
      echo "[DISPATCH BLOCKED/FAILED] ${BRANCH} -> Batch ${BATCH}" >&2
      FAILED=$((FAILED + 1))
    fi
  done
done

echo "Dispatch summary: ${DISPATCHED} succeeded/planned, ${FAILED} blocked/failed."
if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
