from __future__ import annotations

import concurrent.futures
import json
import os
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

from night_shift_portfolio import parse_json_text


STOP_SECONDS = {
    "morning": None,
    "2h": 2 * 60 * 60,
    "6h": 6 * 60 * 60,
    "8h": 8 * 60 * 60,
    "10h": 10 * 60 * 60,
}


def stop_deadline(stop_after: str | None, now: float | None = None) -> float | None:
    seconds = STOP_SECONDS.get(stop_after) if stop_after else None
    if seconds is None:
        return None
    return (time.time() if now is None else now) + seconds


def deadline_reached(deadline: float | None, stop_file: Path | None = None, now: float | None = None) -> bool:
    current = time.time() if now is None else now
    reached = deadline is not None and current >= deadline
    if reached and stop_file and not stop_file.exists():
        stop_file.write_text(
            f"automatic stop limit reached at {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n",
            encoding="utf-8",
        )
    return reached


def stop_recorded_processes(
    ledger: Path, force: bool = False, not_before: float | None = None, now: float | None = None
) -> tuple[int, int]:
    process_file = ledger / "processes.tsv"
    if not process_file.exists():
        return 0, 0
    stopped = 0
    missing = 0
    for line in process_file.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split("\t", 2)
        if not parts or not parts[0].isdigit():
            continue
        pid = int(parts[0])
        if pid <= 1:
            continue
        if not_before is not None:
            try:
                recorded_at = int(parts[1])
            except (IndexError, ValueError):
                missing += 1
                continue
            current = time.time() if now is None else now
            if recorded_at < not_before - 60 or recorded_at > current + 60:
                missing += 1
                continue
        try:
            os.killpg(pid, signal.SIGKILL if force else signal.SIGTERM)
            stopped += 1
        except ProcessLookupError:
            missing += 1
        except PermissionError:
            missing += 1
    return stopped, missing


def cancel_pending_workers(ledger: Path, pending, sleep=time.sleep, wait=concurrent.futures.wait) -> None:
    stopped, _ = stop_recorded_processes(ledger)
    if stopped:
        sleep(0.25)
        stop_recorded_processes(ledger, force=True)
    for future in pending:
        future.cancel()
    if pending:
        wait(list(pending), timeout=2)


def directory_size(path: Path) -> int:
    total = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
    except OSError:
        pass
    return total


def cleanup_candidates(root: Path, days: int, now: float | None = None) -> list[Path]:
    """Only completed, reviewed Night Shift ledgers may be reclaimed."""
    if not root.exists():
        return []
    threshold = (time.time() if now is None else now) - days * 24 * 3600
    candidates = []
    for path in root.iterdir():
        if not path.is_dir() or not path.name.startswith("night-shift-"):
            continue
        if not (path / "morning.md").exists() or not (path / "REVIEWED").exists():
            continue
        try:
            if path.stat().st_mtime < threshold:
                candidates.append(path)
        except OSError:
            continue
    return sorted(candidates, key=lambda path: path.stat().st_mtime)


def active_autopilot(state_path: Path) -> dict:
    try:
        active = parse_json_text(state_path.read_text(encoding="utf-8"), {})
    except OSError:
        return {}
    try:
        os.kill(int(active.get("pid", 0)), 0)
        return active
    except (OSError, ValueError, TypeError):
        return {}


def recover_stale_autopilot(state_path: Path, overnight_root: Path) -> dict:
    """Close a crashed controller ledger without trusting paths from its state file."""
    if not state_path.exists():
        return {"status": "none"}
    if state_path.is_symlink():
        return {"status": "unsafe", "reason": "active state is a symlink"}
    pid = 0
    try:
        state = parse_json_text(state_path.read_text(encoding="utf-8"), {})
        if not isinstance(state, dict):
            return {"status": "unsafe", "reason": "active state is not an object"}
        pid = int(state.get("pid", 0))
        if pid > 1:
            os.kill(pid, 0)
            return {"status": "active", "pid": pid}
    except ProcessLookupError:
        pass
    except PermissionError:
        return {"status": "active", "pid": pid}
    except FileNotFoundError:
        return {"status": "none"}
    except (OSError, ValueError, TypeError):
        state = {}

    root = overnight_root.resolve()
    ledger = Path(str(state.get("ledger") or "")).expanduser()
    try:
        resolved = ledger.resolve()
    except OSError:
        return {"status": "unsafe", "reason": "stale ledger path cannot be resolved"}
    if (
        not state.get("ledger")
        or ledger.is_symlink()
        or not resolved.is_dir()
        or resolved.parent != root
        or not resolved.name.startswith("night-shift-")
    ):
        return {"status": "unsafe", "reason": "stale ledger is outside the Night Shift ledger root"}

    started_at = None
    try:
        started_at = datetime.fromisoformat(str(state.get("started_at"))).timestamp()
    except (TypeError, ValueError):
        pass
    current_time = time.time()
    recent_session = started_at is not None and 0 <= current_time - started_at <= 12 * 3600
    stopped, missing = stop_recorded_processes(
        resolved, not_before=started_at if recent_session else current_time + 1, now=current_time
    )
    if stopped:
        time.sleep(0.25)
        force_stopped, force_missing = stop_recorded_processes(
            resolved, force=True, not_before=started_at, now=current_time
        )
        stopped += force_stopped
        missing += force_missing
    recovered_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (resolved / "STOP").write_text(f"controller crash recovered at {recovered_at}\n", encoding="utf-8")
    recovery = {
        "status": "RECOVERED_AFTER_CRASH",
        "controller_pid": pid if pid > 1 else None,
        "recovered_at": recovered_at,
        "worker_signals_sent": stopped,
        "workers_already_gone": missing,
        "worker_cleanup_scope": "recent-controller-session" if recent_session else "skipped-stale-or-undated-session",
    }
    (resolved / "crash-recovery.json").write_text(
        json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    morning = resolved / "morning.md"
    existing = morning.read_text(encoding="utf-8", errors="replace") if morning.exists() else ""
    existing = existing.replace("Status: GREEN", "Status: YELLOW", 1)
    if "Status:" not in existing:
        existing = "Status: YELLOW\n\n" + existing
    existing += (
        "\n## Crash recovery\n\n"
        "The previous controller stopped unexpectedly. Night Shift stopped its recorded workers "
        "and preserved this ledger for review. A new shift may now start safely.\n"
    )
    morning.write_text(existing, encoding="utf-8")
    state_path.unlink(missing_ok=True)
    return {**recovery, "status": "recovered", "ledger": str(resolved)}
