"""Command runner and ledger path helpers."""
from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from night_shift_paths import OVERNIGHT_ROOT, cli_attr, cli_module


@dataclass
class CmdResult:
    command: str
    rc: int
    stdout: str
    stderr: str
    timed_out: bool = False


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_cmd(args, cwd=None, timeout=60, env=None, pid_log: Path | None = None) -> CmdResult:
    command = " ".join(str(a) for a in args)
    try:
        proc = subprocess.Popen(
            [str(a) for a in args],
            cwd=str(cwd) if cwd else None,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        if pid_log:
            with pid_log.open("a", encoding="utf-8") as f:
                f.write(f"{proc.pid}\t{int(time.time())}\t{command}\n")
        stdout, stderr = proc.communicate(timeout=timeout)
        return CmdResult(command, proc.returncode, stdout, stderr)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            stdout, stderr = proc.communicate(timeout=5)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
            stdout, stderr = exc.stdout or "", exc.stderr or ""
        return CmdResult(
            command,
            124,
            stdout or "",
            stderr or f"timed out after {timeout}s",
            timed_out=True,
        )
    except FileNotFoundError as exc:
        return CmdResult(command, 127, "", str(exc))


def create_ledger(mode: str) -> Path:
    overnight = cli_attr("OVERNIGHT_ROOT", OVERNIGHT_ROOT)
    overnight.mkdir(parents=True, exist_ok=True)
    stamp = now_stamp()
    cli = cli_module()
    if cli is not None and hasattr(cli, "now_stamp"):
        stamp = cli.now_stamp()
    base = overnight / f"night-shift-{stamp}-{mode}"
    ledger = base
    for index in range(2, 100):
        try:
            ledger.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            ledger = overnight / f"{base.name}-{index}"
    else:
        raise FileExistsError(f"could not create unique ledger under {overnight}")
    (ledger / "artifacts").mkdir()
    return ledger


def latest_ledger(completed_only: bool = False) -> Path | None:
    overnight = cli_attr("OVERNIGHT_ROOT", OVERNIGHT_ROOT)
    if not overnight.exists():
        return None
    ledgers = sorted(
        [
            p
            for p in overnight.iterdir()
            if p.is_dir() and (p.name.startswith("night-shift-") or p.name.startswith("tokenmaxx-"))
        ],
        key=lambda p: p.stat().st_mtime,
    )
    if completed_only:
        completed = [path for path in ledgers if (path / "morning.md").exists()]
        if completed:
            ledgers = completed
    return ledgers[-1] if ledgers else None


def select_ledger(args, completed_only: bool = False) -> Path | None:
    if getattr(args, "ledger", None) and getattr(args, "latest", False):
        return None
    if getattr(args, "ledger", None):
        return Path(args.ledger).expanduser().resolve()
    if getattr(args, "latest", False):
        return cli_attr("latest_ledger", latest_ledger)(completed_only=completed_only)
    return None


def repo_root(repo: str | None) -> Path | None:
    if not repo:
        return None
    path = Path(repo).expanduser().resolve()
    if not path.exists():
        return path
    runner = cli_attr("run_cmd", run_cmd)
    result = runner(["git", "-C", path, "rev-parse", "--show-toplevel"], timeout=20)
    if result.rc != 0:
        return path
    return Path(result.stdout.strip())
