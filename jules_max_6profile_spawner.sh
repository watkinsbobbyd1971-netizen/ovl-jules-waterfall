#!/usr/bin/env bash
# ==============================================================================
# OVL JULES SINGLE-BRANCH ACCOUNT-AWARE SPAWNER
# Bounded, observable, dry-run by default across reconciled canonical accounts
# ==============================================================================
set -euo pipefail

REPO="watkinsbobbyd1971-netizen/ovl-jules-waterfall"
BRANCH="${1:-profile-6-global-all20}"
START_BATCH="${2:-1}"
END_BATCH="${3:-10}"
LIVE_MODE="${4:-}"

LIVE_FLAG=()
if [ "$LIVE_MODE" = "--live" ]; then
  LIVE_FLAG=("--live")
fi

# Reconcile branch to account metadata
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISPATCHER="${SCRIPT_DIR}/ovl_jules_dispatch.py"

PROFILE_N="$(echo "$BRANCH" | sed -E 's/^profile-([0-9]+).*/\1/')"

echo "Evaluating parallel Jules cloud VM sessions on $REPO ($BRANCH) for batches $START_BATCH..$END_BATCH (Dry-run default)"

FAILED=0
DISPATCHED=0

for i in $(seq -f "%02g" "$START_BATCH" "$END_BATCH"); do
  PROMPT="Read AGENTS.md and run python3 jules_waterfall_worker.py $i with zero external network calls or questions, and commit ONLY output/profile-${PROFILE_N}/batch_${i}_v3.jsonl directly to this branch; never modify shared root files."
  MANIFEST_CLAIM="batch_${i}_${BRANCH}"

  if python3 "${DISPATCHER}" \
    --repo "$REPO" \
    --branch "$BRANCH" \
    --profile-n "$PROFILE_N" \
    --manifest "$MANIFEST_CLAIM" \
    --prompt "$PROMPT" \
    ${LIVE_FLAG[@]+"${LIVE_FLAG[@]}"}; then
    DISPATCHED=$((DISPATCHED + 1))
  else
    echo "[DISPATCH BLOCKED/FAILED] $BRANCH -> Batch $i" >&2
    FAILED=$((FAILED + 1))
  fi
done

echo "Dispatch summary for $BRANCH: ${DISPATCHED} succeeded/planned, ${FAILED} blocked/failed."
if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
