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
    runtime: str = ""


def sandbox_runtime() -> str:
    """Prefer Docker rootless, otherwise use Podman when its engine is live."""
    return shutil.which("docker") or shutil.which("podman") or ""


def detect_sandbox(run_cmd: Callable) -> SandboxStatus:
    docker = shutil.which("docker")
    if docker:
        info = run_cmd([docker, "info", "--format", "{{json .SecurityOptions}}"], timeout=20)
        if info.rc == 0 and "rootless" in (info.stdout or "").lower():
            return SandboxStatus(True, "Docker rootless sandbox is ready", "docker")
    podman = shutil.which("podman")
    if podman:
        info = run_cmd([podman, "info", "--format", "{{.Host.Security.Rootless}}"], timeout=20)
        if info.rc == 0 and "true" in (info.stdout or "").lower():
            return SandboxStatus(True, "Podman rootless sandbox is ready", "podman")
        return SandboxStatus(False, "Podman is installed but its rootless machine is not ready; execution is disabled", "podman")
    return SandboxStatus(False, "No supported container runtime is installed; execution is disabled")


def fixed_patch_script() -> str:
    """Controller-owned shell only; no repo or model text is interpolated."""
    return (
        "set -eu; cp -a /source/. /work/; cd /work; "
        "git apply --whitespace=error /input/candidate.patch; git diff --check; "
        "git diff --name-only > /artifacts/changed-paths.txt; "
        "git diff --binary > /artifacts/applied.patch; set +e; \"$@\" > /artifacts/verification.txt 2>&1; "
        "rc=$?; printf '%s\\n' \"$rc\" > /artifacts/verification.rc; exit \"$rc\""
    )


def sandbox_patch_command(
    source: Path,
    patch: Path,
    artifacts: Path,
    command: tuple[str, ...],
    profile: RepoProfile,
) -> list[str]:
    """Build the only writable-patch command Night Shift permits.

    Source and patch are read-only. The writable workspace lives only in the
    container tmpfs; the artifact directory receives logs and a candidate diff.
    """
    runtime = sandbox_runtime() or "docker"
    return [
        runtime, "run", "--rm", "--pull", "never", "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", str(profile.max_pids), "--cpus", str(profile.max_cpu),
        "--memory", f"{profile.max_memory_mb}m", "--tmpfs", "/work:rw,noexec,nosuid,size=512m,uid=65534,gid=65534,mode=700",
        "--volume", f"{source.resolve()}:/source:ro", "--volume", f"{patch.resolve()}:/input/candidate.patch:ro",
        "--volume", f"{artifacts.resolve()}:/artifacts:rw", "--workdir", "/work",
        "--env", "HOME=/tmp", "--env", "GIT_CONFIG_NOSYSTEM=1", profile.image,
        "sh", "-ceu", fixed_patch_script(), "night-shift-verify", *command,
    ]


def sandbox_command(repo: Path, command: tuple[str, ...], profile: RepoProfile) -> list[str]:
    """Run with no host credentials/network and bounded resources.

    The repo mount is intentionally read-only. A future patch worker must write
    its patch to a separate, explicitly mounted artifact directory.
    """
    runtime = sandbox_runtime() or "docker"
    home = "/tmp/night-shift-home"
    return [
        runtime, "run", "--rm", "--pull", "never", "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", str(profile.max_pids), "--cpus", str(profile.max_cpu),
        "--memory", f"{profile.max_memory_mb}m", "--tmpfs", f"{home}:rw,noexec,nosuid,size=64m",
        "--workdir", "/workspace", "--volume", f"{repo.resolve()}:/workspace:ro",
        "--env", f"HOME={home}", "--env", "GIT_CONFIG_NOSYSTEM=1",
        profile.image, *command,
    ]
