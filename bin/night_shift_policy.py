"""Trusted policy parsing for Night Shift.

Repository content is untrusted. This module deliberately accepts only a small,
data-only profile format before Night Shift is allowed to execute anything.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROFILE_NAME = ".night-shift.json"
PROFILE_VERSION = 1
SAFE_TRUST = {"owned"}
ALL_TRUST = SAFE_TRUST | {"owned-pr", "collaborator-pr", "fork", "unknown"}
PROTECTED_PATHS = {
    ".night-shift.json", ".github", ".gitignore", ".env", ".env.local",
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "pyproject.toml", "poetry.lock", "Pipfile", "Pipfile.lock", "Makefile",
    "Cargo.toml", "Cargo.lock", "Gemfile", "go.mod", "go.sum",
}
SHELL_METACHARACTERS = re.compile(r"[;&|`$<>(){}\n\r]")
IMAGE_DIGEST = re.compile(r"^(?:[a-z0-9./_-]+@)?sha256:[a-f0-9]{64}$")


@dataclass(frozen=True)
class RepoProfile:
    trust: str
    execution_enabled: bool
    commands: tuple[tuple[str, ...], ...]
    allowed_paths: tuple[str, ...]
    protected_paths: tuple[str, ...]
    max_cpu: float
    max_memory_mb: int
    max_pids: int
    max_seconds: int
    image: str
    external_approval: bool = False
    approved_remote: str = ""

    @property
    def may_execute(self) -> bool:
        return self.trust in SAFE_TRUST and self.execution_enabled and bool(self.commands) and bool(self.image)


def command_display(command: tuple[str, ...] | list[str]) -> str:
    return " ".join(command)


def validate_command(value: Any) -> tuple[str, ...] | None:
    """Validate argv only. Shell strings and control characters never qualify."""
    if not isinstance(value, list) or not value or len(value) > 12:
        return None
    parts: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item or len(item) > 240:
            return None
        if item.startswith("-") and not parts:
            return None
        if SHELL_METACHARACTERS.search(item):
            return None
        parts.append(item)
    return tuple(parts)


def _safe_paths(raw: Any, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return fallback
    values = []
    for path in raw:
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts:
            continue
        values.append(path.rstrip("/"))
    return tuple(dict.fromkeys(values)) or fallback


def parse_repo_profile(raw: Any) -> tuple[RepoProfile | None, str]:
    if not isinstance(raw, dict) or raw.get("version") != PROFILE_VERSION:
        return None, f"{PROFILE_NAME} must set version to {PROFILE_VERSION}"
    trust = raw.get("trust", "unknown")
    if trust not in ALL_TRUST:
        return None, f"invalid trust class: {trust!r}"
    commands = tuple(command for item in raw.get("commands", []) if (command := validate_command(item)))
    if raw.get("commands") and not commands:
        return None, "profile commands must be safe argv arrays, never shell strings"
    limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
    image = raw.get("image", "")
    if image and (not isinstance(image, str) or not IMAGE_DIGEST.fullmatch(image)):
        return None, "profile image must be a pinned OCI sha256 digest"
    try:
        profile = RepoProfile(
            trust=trust,
            execution_enabled=raw.get("execution") == "sandbox-only",
            commands=commands,
            allowed_paths=_safe_paths(raw.get("allowed_paths"), ("src", "lib", "app", "tests", "test")),
            protected_paths=_safe_paths(raw.get("protected_paths"), tuple(sorted(PROTECTED_PATHS))),
            max_cpu=min(4.0, max(0.25, float(limits.get("cpu", 2)))),
            max_memory_mb=min(8192, max(256, int(limits.get("memory_mb", 2048)))),
            max_pids=min(256, max(16, int(limits.get("pids", 128)))),
            max_seconds=min(1800, max(30, int(limits.get("seconds", 900)))),
            image=image,
        )
    except (TypeError, ValueError):
        return None, "profile limits must be sensible numbers"
    if profile.execution_enabled and not profile.commands:
        return None, "sandbox-only execution needs at least one approved argv command"
    if profile.execution_enabled and not profile.image:
        return None, "sandbox-only execution needs a pinned local runner image"
    return profile, "profile loaded"


def load_repo_profile(repo: Path) -> tuple[RepoProfile | None, str]:
    profile_path = repo / PROFILE_NAME
    if not profile_path.is_file():
        return None, f"missing {PROFILE_NAME}; execution stays disabled"
    try:
        raw = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, f"could not read {PROFILE_NAME}: {exc}"
    return parse_repo_profile(raw)


def path_is_protected(path: str, protected_paths: tuple[str, ...] = tuple(PROTECTED_PATHS)) -> bool:
    candidate = Path(path)
    return any(path == item or item in candidate.parts for item in protected_paths)


def path_is_allowed(path: str, allowed_paths: tuple[str, ...]) -> bool:
    return any(path == item or path.startswith(item.rstrip("/") + "/") for item in allowed_paths)
