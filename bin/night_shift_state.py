"""Durable task state, cooldowns, and single-run locking."""
from __future__ import annotations

import json
import fcntl
import os
import shutil
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


STATES = ("DISCOVERED", "GAP_CONFIRMED", "REPRODUCED", "DIAGNOSED", "PATCHED", "VERIFIED", "REVIEWED", "PROMOTED", "REJECTED")
ALLOWED = {
    "DISCOVERED": {"GAP_CONFIRMED", "REPRODUCED", "REJECTED"},
    "GAP_CONFIRMED": {"DIAGNOSED", "REJECTED"},
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


def rejection_count(path: Path, repo: str, head: str) -> int:
    count = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if item.get("repo") == repo and item.get("head") == head and item.get("state") == "REJECTED":
            count += 1
    return count


def fresh_explicit_goal_tasks(
    tasks: list[dict], attempts: dict[str, dict], guidance: str, goal: str
) -> list[dict]:
    """Return only one never-attempted mission when a user names a new goal.

    The revision circuit still blocks automatic retries and previously rejected
    work. A concrete new mission is a deliberate user request, so it gets one
    fresh chance without reopening the old queue.
    """
    if guidance != "goal" or not str(goal or "").strip():
        return []
    return [
        task for task in tasks
        if task.get("slug") == "mission-brief"
        and task.get("fingerprint")
        and task.get("fingerprint") not in attempts
    ]


def cooldown_seconds(rejections: int) -> int:
    return min(7 * 24 * 3600, 900 * (2 ** max(0, rejections - 1)))


def may_attempt(previous: dict | None, fingerprint: str, head: str, now: float | None = None) -> tuple[bool, str]:
    if not previous:
        return True, "new task"
    if previous.get("task_revision", previous.get("head")) != head:
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


def latest_states(path: Path) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return latest
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        fingerprint = event.get("fingerprint")
        if fingerprint and event.get("state") in STATES:
            latest[fingerprint] = event
    return latest


def record_state(path: Path, fingerprint: str, target: str, **details) -> dict:
    """Append one validated lifecycle event and return it.

    A state may be recorded more than once to attach additional evidence, but
    forward movement must follow the explicit state graph.
    """
    if target not in STATES:
        raise ValueError(f"unknown task state: {target}")
    previous = latest_states(path).get(fingerprint)
    current = previous.get("state") if previous else ""
    if not current and target != "DISCOVERED":
        raise ValueError(f"task {fingerprint} must start at DISCOVERED")
    if current and target != current and not transition(current, target):
        raise ValueError(f"invalid task transition: {current} -> {target}")
    event = {
        "at": utc_now(),
        "fingerprint": fingerprint,
        "state": target,
        **details,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


@contextmanager
def exclusive_lock(path: Path) -> Iterator[bool]:
    """Kernel-backed nonblocking lock; the file remains but ownership dies with the process."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        legacy_active = False
        for attempt in range(4):
            try:
                pid = int((path / "pid").read_text(encoding="utf-8"))
                os.kill(pid, 0)
                legacy_active = True
                break
            except ProcessLookupError:
                break
            except PermissionError:
                legacy_active = True
                break
            except (FileNotFoundError, NotADirectoryError, ValueError):
                if attempt < 3:
                    time.sleep(0.05)
                    if not path.exists() or not path.is_dir():
                        break
                    continue
                break
        if legacy_active:
            yield False
            return
        if path.is_dir():
            quarantine = path.with_name(f"{path.name}.stale-{os.getpid()}-{time.time_ns()}")
            try:
                path.rename(quarantine)
            except (FileNotFoundError, FileExistsError, OSError):
                yield False
                return
            shutil.rmtree(quarantine, ignore_errors=True)

    try:
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    except IsADirectoryError:
        yield False
        return
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())
        os.fsync(fd)
        yield True
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
