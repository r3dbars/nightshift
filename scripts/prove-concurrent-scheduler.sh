#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
controller_pid=""
cleanup() {
  [[ -z "$controller_pid" ]] || kill -KILL "$controller_pid" 2>/dev/null || true
  rm -rf "$tmp"
}
trap cleanup EXIT

home="$tmp/codex-home"
repo="$tmp/project"
mkdir -p "$repo"
git -C "$repo" init -q
git -C "$repo" config user.email scheduler-proof@example.invalid
git -C "$repo" config user.name "Scheduler Proof"
printf 'print(42)\n' > "$repo/app.py"
git -C "$repo" add app.py
git -C "$repo" commit -qm initial

CODEX_HOME="$home" "$repo_root/bin/night-shift" start \
  --repo "$repo" --yes --setup-only --skip-smoke >/dev/null
python3 - "$home/night-shift/config.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
config = json.loads(path.read_text(encoding="utf-8"))
config.setdefault("preferences", {}).update({
    "mode": "quiet",
    "scope": "current",
    "local_url": "http://127.0.0.1:9/v1",
    "windows_url": "",
    "privacy_route": "mac-only",
})
path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

config_dir="$home/night-shift"
overnight="$home/maestro/overnight"
old_ledger="$overnight/night-shift-0000-concurrent-autopilot"
mkdir -p "$old_ledger"
printf 'scheduled run\n' > "$old_ledger/UNATTENDED"

python3 - "$config_dir" "$old_ledger" <<'PY' &
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

config = Path(sys.argv[1])
ledger = Path(sys.argv[2])
lock = config / "autopilot.lock"
lock.mkdir()
(lock / "pid").write_text(str(os.getpid()), encoding="utf-8")
(config / "active-autopilot.json").write_text(json.dumps({
    "pid": os.getpid(), "ledger": str(ledger),
    "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
}) + "\n", encoding="utf-8")
while True:
    time.sleep(1)
PY
controller_pid=$!
for _ in $(seq 1 50); do
  [[ -s "$config_dir/active-autopilot.json" ]] && break
  sleep 0.1
done
test -s "$config_dir/active-autopilot.json"

before="$(find "$overnight" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
first="$tmp/first-nightly.out"
CODEX_HOME="$home" "$repo_root/bin/night-shift" nightly --once >"$first" 2>&1
after="$(find "$overnight" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
test "$before" = "$after"
grep -Fq "NIGHTSHIFT_NIGHTLY: GREEN | skipped | shift already running" "$first"
grep -Fq '"status": "SKIPPED_ACTIVE"' "$config_dir/last-nightly.json"

kill -KILL "$controller_pid"
wait "$controller_pid" 2>/dev/null || true
controller_pid=""

second="$tmp/second-nightly.out"
CODEX_HOME="$home" "$repo_root/bin/night-shift" nightly --once >"$second" 2>&1 || true
grep -Fq "Recovered prior crashed shift:" "$second"
grep -Fq "NIGHTSHIFT_AUTOPILOT:" "$second"
test -s "$old_ledger/crash-recovery.json"
test ! -e "$config_dir/active-autopilot.json"
test ! -e "$config_dir/autopilot.lock"
if grep -Fq '"status": "SKIPPED_ACTIVE"' "$config_dir/last-nightly.json"; then
  echo "next scheduled launch was incorrectly left as skipped" >&2
  exit 1
fi

echo "CONCURRENT_SCHEDULER_PROOF: GREEN | overlap skipped without a ledger, next nightly recovered and ran"
