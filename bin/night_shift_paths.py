"""Resolved Night Shift homes, installed-tool lookup, and shared Mac paths."""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
HOME = Path.home()
VERSION = "0.1.0"


def resolve_data_home() -> Path:
    """Prefer an explicit home, then XDG, then a legacy ~/.codex install."""
    nightshift_home = os.environ.get("NIGHTSHIFT_HOME")
    if nightshift_home:
        return Path(nightshift_home).expanduser()
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg).expanduser() / "nightshift"
    legacy = HOME / ".codex"
    if (legacy / "night-shift").exists() or (legacy / "bin" / "night-shift").exists():
        return legacy
    return HOME / ".local" / "share" / "nightshift"


NIGHTSHIFT_HOME = resolve_data_home()
CODEX_HOME = NIGHTSHIFT_HOME
BIN = CODEX_HOME / "bin"
OVERNIGHT_ROOT = CODEX_HOME / "maestro" / "overnight"
CONFIG_DIR = CODEX_HOME / "night-shift"
CONFIG_PATH = CONFIG_DIR / "config.json"
REPO_APPROVALS_ROOT = CONFIG_DIR / "repo-approvals"
DEPENDENCY_CACHE_ROOT = CONFIG_DIR / "dependency-cache"
FEEDBACK_PATH = CONFIG_DIR / "feedback.jsonl"
REVIEW_OUTCOMES_PATH = CONFIG_DIR / "review-outcomes.jsonl"
TASK_HISTORY_PATH = CONFIG_DIR / "task-history.jsonl"
REPO_OUTCOMES_PATH = CONFIG_DIR / "repo-outcomes.jsonl"
TASK_ATTEMPTS_PATH = CONFIG_DIR / "task-attempts.jsonl"
AUTOPILOT_LOCK_PATH = CONFIG_DIR / "autopilot.lock"
REPO_CACHE_ROOT = CONFIG_DIR / "repos"
WORKTREE_ROOT = CONFIG_DIR / "worktrees"
AUTOPILOT_STATE_PATH = CONFIG_DIR / "active-autopilot.json"
DEFAULT_LOCAL_URL = "http://localhost:1234/v1"
DEFAULT_LOCAL_MODEL = "phi-4-mini-instruct"
OLLAMA_LOCAL_URL = "http://localhost:11434/v1"
DEFAULT_WINDOWS_URL = ""
DEFAULT_WINDOWS_MODEL = "qwen3-coder:30b"
LAN_DISCOVERY_MAX_HOSTS = 24
LAN_DISCOVERY_MAX_SECONDS = 8
LAN_DISCOVERY_REQUEST_TIMEOUT = 1.2


_HOST = None


def cli_module():
    if _HOST is not None:
        return _HOST
    return sys.modules.get("night_shift_cli")


def cli_attr(name: str, fallback):
    cli = cli_module()
    if cli is not None and hasattr(cli, name):
        return getattr(cli, name)
    return fallback


def runtime_tool(name: str) -> Path:
    """Use the installed helper, or the matching helper beside a checkout run."""
    installed = cli_attr("BIN", BIN) / name
    if installed.exists() and os.access(installed, os.X_OK):
        return installed
    bundled = cli_attr("SCRIPT_DIR", SCRIPT_DIR) / name
    if bundled.exists() and os.access(bundled, os.X_OK):
        return bundled
    return installed


def shared_macos_codex_path(root: Path) -> Path:
    """Move temporary Mac state to a Colima-shared home-backed path."""
    system = cli_attr("platform", platform).system()
    if system != "Darwin" or str(root).startswith("/Users/"):
        return root
    user = os.environ.get("USER", "")
    real_home = Path("/Users") / user if user else Path()
    if user and real_home.is_dir():
        return real_home / ".codex" / "night-shift" / root.name
    return root


def shared_worktree_root() -> Path:
    """Keep disposable worktrees on a macOS path that Colima can mount."""
    return shared_macos_codex_path(cli_attr("WORKTREE_ROOT", WORKTREE_ROOT))


def shared_repo_cache_root() -> Path:
    return shared_macos_codex_path(cli_attr("REPO_CACHE_ROOT", REPO_CACHE_ROOT))


def shared_dependency_cache_root() -> Path:
    return shared_macos_codex_path(cli_attr("DEPENDENCY_CACHE_ROOT", DEPENDENCY_CACHE_ROOT))
