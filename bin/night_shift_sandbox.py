"""Fail-closed container runner for executing approved repo checks."""
from __future__ import annotations

import json
import os
import platform
import re
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


def runner_context() -> Path:
    return Path(__file__).resolve().parents[1] / "containers" / "runner"


def runner_build_command(runtime: str, context: Path) -> list[str | Path]:
    args: list[str | Path] = [runtime, "build"]
    # Explicit setup may fetch the digest-pinned base; overnight runs never pull.
    if Path(runtime).name == "podman":
        args.append("--pull=missing")
    return [*args, "--tag", "night-shift-runner:local", "--file", context / "Containerfile", context]


def build_runner_image(run_cmd: Callable) -> tuple[bool, str]:
    """Build the reviewed local runner and return its immutable content ID."""
    status = detect_sandbox(run_cmd)
    if not status.available:
        return False, status.detail
    context = runner_context()
    runtime = status.runtime
    built = run_cmd(runner_build_command(runtime, context), timeout=900)
    if built.rc != 0:
        return False, (built.stderr or built.stdout or "runner build failed").strip()[:600]
    inspected = run_cmd([runtime, "image", "inspect", "night-shift-runner:local", "--format", "{{.Id}}"], timeout=60)
    image = inspected.stdout.strip()
    if re.fullmatch(r"[a-f0-9]{64}", image):
        image = f"sha256:{image}"
    if inspected.rc != 0 or not image.startswith("sha256:") or len(image) != 71:
        return False, "runner built but did not return an immutable image ID"
    return True, image


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
        machines = run_cmd([podman, "machine", "list", "--format", "json"], timeout=20)
        try:
            rows = json.loads(machines.stdout) if machines.rc == 0 else []
        except (TypeError, json.JSONDecodeError):
            rows = []
        if isinstance(rows, list) and rows:
            machine = next((row for row in rows if row.get("Default")), rows[0])
            name = str(machine.get("Name") or "podman-machine-default")
            if machine.get("Running"):
                detail = (
                    f"Podman machine '{name}' is running but its engine is unreachable; "
                    f"run `podman machine stop {name}` then `podman machine start {name}`"
                )
            else:
                detail = f"Podman machine '{name}' is stopped; run `podman machine start {name}`"
            return SandboxStatus(False, detail + "; execution is disabled", "podman")
        if platform.system() == "Darwin":
            detail = "Podman is installed but no machine is ready; run `podman machine init --now`"
        else:
            detail = "Podman is installed but its rootless engine is unreachable; start the user Podman service"
        return SandboxStatus(False, detail + "; execution is disabled", "podman")
    return SandboxStatus(False, "No supported container runtime is installed; execution is disabled")


def fixed_patch_script() -> str:
    """Controller-owned shell only; no repo or model text is interpolated."""
    return (
        "set -eu; cp -a /source/. /work/; cd /work; rm -rf .git; git init -q; "
        "git config user.email night-shift@localhost; git config user.name 'Night Shift'; "
        "git add -A; git commit -qm baseline; "
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
    tmpfs_options = "rw,noexec,nosuid,size=512m,mode=700"
    if Path(runtime).name != "podman":
        tmpfs_options += ",uid=65534,gid=65534"
    return [
        runtime, "run", "--rm", "--pull", "never", "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", str(profile.max_pids), "--cpus", str(profile.max_cpu),
        "--memory", f"{profile.max_memory_mb}m", "--tmpfs", f"/work:{tmpfs_options}",
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
