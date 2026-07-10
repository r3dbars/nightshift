"""Fail-closed container runner for executing approved repo checks."""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from night_shift_policy import RepoProfile


@dataclass(frozen=True)
class SandboxStatus:
    available: bool
    detail: str


def detect_sandbox(run_cmd: Callable) -> SandboxStatus:
    docker = shutil.which("docker")
    if not docker:
        return SandboxStatus(False, "Docker is not installed; execution is disabled")
    info = run_cmd([docker, "info", "--format", "{{json .SecurityOptions}}"], timeout=20)
    if info.rc != 0 or "rootless" not in (info.stdout or "").lower():
        return SandboxStatus(False, "Docker rootless mode is required; execution is disabled")
    return SandboxStatus(True, "Docker rootless sandbox is ready")


def sandbox_command(repo: Path, command: tuple[str, ...], profile: RepoProfile, image: str = "python:3.12-alpine") -> list[str]:
    """Run with no host credentials/network and bounded resources.

    The repo mount is intentionally read-only. A future patch worker must write
    its patch to a separate, explicitly mounted artifact directory.
    """
    docker = shutil.which("docker") or "docker"
    home = "/tmp/night-shift-home"
    return [
        docker, "run", "--rm", "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", str(profile.max_pids), "--cpus", str(profile.max_cpu),
        "--memory", f"{profile.max_memory_mb}m", "--tmpfs", f"{home}:rw,noexec,nosuid,size=64m",
        "--workdir", "/workspace", "--volume", f"{repo.resolve()}:/workspace:ro",
        "--env", f"HOME={home}", "--env", "GIT_CONFIG_NOSYSTEM=1",
        image, *command,
    ]

