#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d -t night-shift-soak.XXXXXX)"
trap 'rm -rf "$tmp"' EXIT

home="$tmp/codex-home"
repo="$tmp/project"
mkdir -p "$repo"
git -C "$repo" init -q
git -C "$repo" config user.email soak-proof@example.invalid
git -C "$repo" config user.name "Night Shift Soak Proof"
printf 'print(42)\n' > "$repo/app.py"
git -C "$repo" add app.py
git -C "$repo" commit -qm initial

HOME="$tmp" SHELL=/bin/bash "$repo_root/install.sh" --codex-home "$home" --no-path >/dev/null

CODEX_HOME="$home" "$home/bin/night-shift" start \
  --repo "$repo" --yes --setup-only --skip-smoke >/dev/null

duration="${NIGHT_SHIFT_SOAK_SECONDS:-36000}"
kill_after="${NIGHT_SHIFT_SOAK_KILL_AFTER_SECONDS:-3}"
test "$duration" -gt 0
test "$kill_after" -gt 0
proof_path="${NIGHT_SHIFT_SOAK_PROOF_PATH:-}"

python3 - "$repo_root" "$home" "$repo" "$duration" "$kill_after" "$proof_path" <<'PY'
import json
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path

root, home, repo, duration, kill_after, proof_path = sys.argv[1:]
duration = int(duration)
kill_after = int(kill_after)
interval = int(os.environ.get("NIGHT_SHIFT_SOAK_INTERVAL_SECONDS", "60"))
if interval <= 0:
    raise SystemExit("NIGHT_SHIFT_SOAK_INTERVAL_SECONDS must be positive")
config = Path(home) / "night-shift"
overnight = Path(home) / "maestro" / "overnight"
active = config / "active-autopilot.json"
common = [
    str(Path(home) / "bin" / "night-shift"), "autopilot",
    "--repo", repo, "--scope", "current", "--mode", "quiet",
    "--permission", "brief", "--guidance", "scan", "--stop-after", "10h",
    "--timeout", "2", "--poll-minutes", "1", "--skip-smoke",
    "--local-url", "http://127.0.0.1:9/v1",
]
env = {**os.environ, "CODEX_HOME": home}
started = time.monotonic()
killed = 0
outputs = []
rounds = 0
initial_free = shutil.disk_usage(home).free
minimum_free = initial_free
maximum_ledgers = 0

def launch(extra=()):
    return subprocess.Popen(
        common + list(extra),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )

while time.monotonic() - started < duration:
    rounds += 1
    process = launch()
    deadline = time.monotonic() + kill_after
    ready = False
    while process.poll() is None and time.monotonic() < deadline:
        try:
            state = json.loads(active.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        if state.get("pid") == process.pid:
            ready = True
            break
        time.sleep(0.05)
    if process.poll() is None and ready:
        os.killpg(process.pid, signal.SIGKILL)
        killed += 1
    elif process.poll() is None:
        process.terminate()
    try:
        output, _ = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        output, _ = process.communicate()
    outputs.append(output)
    minimum_free = min(minimum_free, shutil.disk_usage(home).free)
    maximum_ledgers = max(maximum_ledgers, len(list(overnight.glob("night-shift-*"))))
    remaining = duration - (time.monotonic() - started)
    if remaining > 0:
        time.sleep(min(interval, remaining))

final = launch(("--once",))
output, _ = final.communicate(timeout=60)
outputs.append(output)
if final.returncode != 0:
    print("\n".join(outputs), file=sys.stderr)
    raise SystemExit(f"final recovery run failed with rc={final.returncode}")

ledgers = sorted(path for path in overnight.glob("night-shift-*") if path.is_dir())
recovered = [path for path in ledgers if (path / "crash-recovery.json").exists()]
names = [path.name for path in ledgers]
if len(names) != len(set(names)):
    raise SystemExit("duplicate ledger names detected")
if killed and len(recovered) < killed:
    print("\n--- soak controller output ---\n".join(item[-1500:] for item in outputs), file=sys.stderr)
    raise SystemExit(f"only {len(recovered)} crash recoveries recorded for {killed} killed controllers")
if active.exists():
    raise SystemExit("active controller state remained after final run")
if not any("Recovered prior crashed shift:" in item for item in outputs[1:]):
    raise SystemExit("no subsequent controller reported recovering a killed predecessor")

proof = {
    "status": "GREEN",
    "duration_seconds": duration,
    "controller_rounds": rounds,
    "controllers_killed": killed,
    "ledgers": len(ledgers),
    "crash_recoveries": len(recovered),
    "active_state_remaining": active.exists(),
    "initial_free_bytes": initial_free,
    "minimum_free_bytes": minimum_free,
    "maximum_ledger_count": maximum_ledgers,
}
if proof_path:
    destination = Path(proof_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, destination)
print("TEN_HOUR_SOAK_PROOF: GREEN | " + json.dumps(proof, sort_keys=True))
PY
