#!/usr/bin/env bash
# ==============================================================================
# OVL JULES 6-PROFILE MAX CONCURRENCY SPAWNER (60 VMs/PROFILE = 360 CONCURRENT VMs)
# Runs across all 6 Ultra Profiles before Nov 11 Read-Only Cutoff
# ==============================================================================
REPO="watkinsbobbyd1971-netizen/ovl-jules-waterfall"
BRANCHES=(
  "profile-1-cat01-04"
  "profile-2-cat05-08"
  "profile-3-cat09-12"
  "profile-4-cat13-16"
  "profile-5-cat17-20"
  "profile-6-global-all20"
)

echo "Spawning parallel Google Jules cloud VM sessions across all branches..."
for BRANCH in "${BRANCHES[@]}"; do
  PROFILE_N="$(echo "$BRANCH" | sed -E 's/^profile-([0-9]+).*/\1/')"
  for BATCH in $(seq -w 1 10); do
    PROMPT="On branch ${BRANCH}, read AGENTS.md and run python3 jules_waterfall_worker.py ${BATCH} locally with zero external network calls or questions, and commit ONLY output/profile-${PROFILE_N}/batch_${BATCH}_v3.jsonl directly to ${BRANCH}; never modify shared root files."
    if command -v jules &> /dev/null; then
      jules session create --repo "${REPO}" --branch "${BRANCH}" --prompt "${PROMPT}" &
    else
      echo "[QUEUE] ${BRANCH} -> Batch ${BATCH}: ${PROMPT}"
    fi
  done
done
wait
echo "All parallel Jules sessions dispatched!"
