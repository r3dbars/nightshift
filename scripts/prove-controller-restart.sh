#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
controller_pid=""
worker_pid=""
cleanup() {
  [[ -z "$controller_pid" ]] || kill -KILL "$controller_pid" 2>/dev/null || true
  [[ -z "$worker_pid" ]] || kill -KILL -- "-$worker_pid" 2>/dev/null || true
  rm -rf "$tmp"
}
trap cleanup EXIT

home="$tmp/codex-home"
config="$home/night-shift"
overnight="$home/maestro/overnight"
ledger="$overnight/night-shift-crashed-autopilot"
repo="$tmp/project"
mkdir -p "$config" "$ledger" "$repo"
git -C "$repo" init -q
git -C "$repo" config user.email restart-proof@example.invalid
git -C "$repo" config user.name "Restart Proof"
printf 'print(42)\n' > "$repo/app.py"
git -C "$repo" add app.py
git -C "$repo" commit -qm initial

python3 - "$config" "$ledger" <<'PY' &
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

config = Path(sys.argv[1])
ledger = Path(sys.argv[2])
lock = config / "autopilot.lock"
lock.mkdir()
(lock / "pid").write_text(str(os.getpid()), encoding="utf-8")
worker = subprocess.Popen(["sleep", "300"], start_new_session=True)
now = int(time.time())
(ledger / "processes.tsv").write_text(f"{worker.pid}\t{now}\tsleep 300\n", encoding="utf-8")
(config / "active-autopilot.json").write_text(
    json.dumps({
        "pid": os.getpid(),
        "ledger": str(ledger),
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }) + "\n",
    encoding="utf-8",
)
while True:
    time.sleep(1)
PY
controller_pid=$!

for _ in $(seq 1 50); do
  [[ -s "$ledger/processes.tsv" && -s "$config/active-autopilot.json" ]] && break
  sleep 0.1
done
test -s "$ledger/processes.tsv"
worker_pid="$(cut -f1 "$ledger/processes.tsv")"
kill -0 "$worker_pid"
kill -KILL "$controller_pid"
wait "$controller_pid" 2>/dev/null || true
controller_pid=""

output="$tmp/restart.out"
CODEX_HOME="$home" "$repo_root/bin/night-shift" autopilot \
  --repo "$repo" --scope current --mode quiet --permission brief \
  --guidance scan --stop-after 2h --timeout 2 --skip-smoke --once \
  --local-url http://127.0.0.1:9/v1 >"$output" 2>&1 || true

if ! grep -Fq "Recovered prior crashed shift:" "$output"; then
  cat "$output" >&2
  exit 1
fi
grep -Fq "NIGHTSHIFT_AUTOPILOT:" "$output"
test -s "$ledger/crash-recovery.json"
grep -Fq '"status": "RECOVERED_AFTER_CRASH"' "$ledger/crash-recovery.json"
grep -Fq "Status: YELLOW" "$ledger/morning.md"
test -s "$ledger/STOP"
test ! -e "$config/active-autopilot.json"
test ! -e "$config/autopilot.lock"

for _ in $(seq 1 30); do
  if ! kill -0 "$worker_pid" 2>/dev/null; then
    worker_pid=""
    break
  fi
  sleep 0.1
done
if [[ -n "$worker_pid" ]]; then
  echo "orphan worker still running after controller restart: $worker_pid" >&2
  exit 1
fi

echo "CONTROLLER_RESTART_PROOF: GREEN | stale lock reclaimed, orphan stopped, old ledger preserved, new autopilot completed"
