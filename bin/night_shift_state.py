"""Durable task state, cooldowns, and single-run locking."""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


STATES = ("DISCOVERED", "REPRODUCED", "DIAGNOSED", "PATCHED", "VERIFIED", "REVIEWED", "PROMOTED", "REJECTED")
ALLOWED = {
    "DISCOVERED": {"REPRODUCED", "REJECTED"},
    "REPRODUCED": {"DIAGNOSED", "REJECTED"},
    "DIAGNOSED": {"PATCHED", "REJECTED"},
    "PATCHED": {"VERIFIED", "REJECTED"},
    "VERIFIED": {"REVIEWED", "REJECTED"},
    "REVIEWED": {"PROMOTED", "REJECTED"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append_attempt(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"at": utc_now(), **row}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def latest_attempts(path: Path) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return latest
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if item.get("fingerprint"):
            latest[item["fingerprint"]] = item
    return latest


def cooldown_seconds(rejections: int) -> int:
    return min(7 * 24 * 3600, 900 * (2 ** max(0, rejections - 1)))


def may_attempt(previous: dict | None, fingerprint: str, head: str, now: float | None = None) -> tuple[bool, str]:
    if not previous:
        return True, "new task"
    if previous.get("head") != head:
        return True, "repository revision changed"
    if previous.get("state") != "REJECTED":
        return False, "already attempted at this repository revision"
    rejected_at = float(previous.get("epoch", 0))
    delay = cooldown_seconds(int(previous.get("rejections", 1)))
    now = time.time() if now is None else now
    if now < rejected_at + delay:
        return False, f"cooldown active for {int(rejected_at + delay - now)} seconds"
    return True, "cooldown elapsed"


def transition(current: str, target: str) -> bool:
    return target in ALLOWED.get(current, set())


@contextmanager
def exclusive_lock(path: Path) -> Iterator[bool]:
    """Atomic mkdir lock. Stale locks are reclaimed only when their PID is gone."""
    try:
        path.mkdir(parents=True)
        (path / "pid").write_text(str(os.getpid()), encoding="utf-8")
    except FileExistsError:
        try:
            pid = int((path / "pid").read_text(encoding="utf-8"))
            os.kill(pid, 0)
        except (OSError, ValueError):
            for child in path.iterdir():
                child.unlink(missing_ok=True)
            path.rmdir()
            with exclusive_lock(path) as acquired:
                yield acquired
            return
        yield False
        return
    try:
        yield True
    finally:
        for child in path.iterdir():
            child.unlink(missing_ok=True)
        path.rmdir()
