#!/usr/bin/env bash
# ==============================================================================
# OVL 6-PROFILE JULES MAX-OUT SPAWNER (360 CONCURRENT CLOUD VMs / 1,800 TASKS/DAY)
# Repo: watkinsbobbyd1971-netizen/ovl-jules-waterfall
# Branches:
#   Profile 1 (tanishawatkins0125@gmail.com)      -> profile-1-cat01-04
#   Profile 2 (claudevisualdy@gmail.com)          -> profile-2-cat05-08
#   Profile 3 (tanishabobby4life@gmail.com)       -> profile-3-cat09-12
#   Profile 4 (magnificent19710125@gmail.com)     -> profile-4-cat13-16
#   Profile 5 (optimizedvisuallearning@gmail.com) -> profile-5-cat17-20
#   Profile 6 (watkinsbobbyd1971@gmail.com)       -> profile-6-global-all20
# ==============================================================================
set -e
REPO="watkinsbobbyd1971-netizen/ovl-jules-waterfall"
BRANCH="${1:-profile-6-global-all20}"
START_BATCH="${2:-1}"
END_BATCH="${3:-10}"

echo "Spawning parallel Jules cloud VM sessions on $REPO ($BRANCH) for batches $START_BATCH..$END_BATCH"
for i in $(seq -f "%02g" "$START_BATCH" "$END_BATCH"); do
  PROMPT="Read AGENTS.md and run python3 jules_waterfall_worker.py $i with zero external network calls or questions, and commit output/batch_${i}_v3.jsonl directly to this branch."
  if command -v jules >/dev/null 2>&1; then
    jules session create --repo "$REPO" --branch "$BRANCH" --prompt "$PROMPT" &
  else
    echo "[Queue Prompt $i for Browser/Muse]: $PROMPT"
  fi
done
wait
echo "All sessions dispatched for $BRANCH."
