from __future__ import annotations

import concurrent.futures
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


def stop_recorded_processes(ledger: Path, force: bool = False) -> tuple[int, int]:
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
