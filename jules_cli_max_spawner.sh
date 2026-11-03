#!/usr/bin/env bash
# Explicit single-manifest dispatcher entrypoint. No branch/account inference,
# synthetic batch claims, quota assumptions or success counters.
# Supply --acc-id, --branch, --manifest existing.json and --prompt.
# Dry-run is default; --live remains blocked until a verified adapter exists.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/ovl_jules_dispatch.py" "$@"
