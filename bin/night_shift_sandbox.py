"""Fail-closed container runner for executing approved repo checks."""
from __future__ import annotations

import json
import hashlib
import os
import platform
import re
import shutil
import time
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


def live_colima_docker(run_cmd: Callable, docker: str) -> str:
    """Return a verified Colima profile name for this Docker context."""
    if platform.system() != "Darwin" or not shutil.which("colima"):
        return ""
    if not os.environ.get("DOCKER_CONFIG"):
        docker_homes: list[Path] = []
        if os.environ.get("USER"):
            docker_homes.append(Path("/Users") / os.environ["USER"] / ".docker")
        docker_homes.append(Path.home() / ".docker")
        existing_config = next((path for path in docker_homes if path.is_dir()), None)
        if existing_config:
            # A clean proof HOME should not hide the user's existing local
            # Docker context metadata from sandbox discovery.
            os.environ["DOCKER_CONFIG"] = str(existing_config)
    if not os.environ.get("COLIMA_HOME"):
        colima_homes: list[Path] = []
        if os.environ.get("USER"):
            colima_homes.append(Path("/Users") / os.environ["USER"] / ".colima")
        colima_homes.append(Path.home() / ".colima")
        existing_home = next((path for path in colima_homes if path.is_dir()), None)
        if existing_home:
            # Keep clean proof homes isolated while allowing discovery of the
            # user's already-running Colima VM.
            os.environ["COLIMA_HOME"] = str(existing_home)
    context = run_cmd([docker, "context", "show"], timeout=20)
    name = context.stdout.strip() if context.rc == 0 else ""
    if name == "colima":
        profile = "default"
    elif name.startswith("colima-"):
        profile = name.removeprefix("colima-")
    else:
        listed = run_cmd([shutil.which("colima"), "list", "--json"], timeout=20)
        rows: list[dict] = []
        try:
            parsed = json.loads(listed.stdout) if listed.rc == 0 else []
            rows = parsed if isinstance(parsed, list) else [parsed] if isinstance(parsed, dict) else []
        except (TypeError, json.JSONDecodeError):
            for line in listed.stdout.splitlines():
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    rows.append(parsed)
        running = next(
            (
                row for row in rows
                if str(row.get("status") or "").lower() == "running"
                and str(row.get("runtime") or "").lower() == "docker"
            ),
            None,
        )
        if not running:
            return ""
        profile = str(running.get("name") or "")
        context_name = "colima" if profile == "default" else f"colima-{profile}"
        context_info = run_cmd(
            [docker, "--context", context_name, "info", "--format", "{{json .SecurityOptions}}"],
            timeout=20,
        )
        if context_info.rc != 0:
            return ""
        # The context is process-local. It lets a clean proof HOME use the
        # already-running Colima VM without changing the user's Docker config.
        os.environ.setdefault("DOCKER_CONTEXT", context_name)
    status = run_cmd([shutil.which("colima"), "status", "--profile", profile, "--json"], timeout=20)
    try:
        detail = json.loads(status.stdout) if status.rc == 0 else {}
    except (TypeError, json.JSONDecodeError):
        return ""
    socket_candidates = {Path.home()}
    # A temporary HOME is useful for clean install proofs, but Colima keeps
    # its VM socket under the real macOS user's home directory.
    if platform.system() == "Darwin" and os.environ.get("USER"):
        socket_candidates.add(Path("/Users") / os.environ["USER"])
    expected_sockets = {
        f"unix://{home}/.colima/{profile}/docker.sock"
        for home in socket_candidates
    }
    if (
        detail.get("runtime") == "docker"
        and str(detail.get("driver") or "").startswith("macOS ")
        and detail.get("docker_socket") in expected_sockets
    ):
        return profile
    return ""


def detect_sandbox(run_cmd: Callable) -> SandboxStatus:
    docker = shutil.which("docker")
    if docker:
        info = run_cmd([docker, "info", "--format", "{{json .SecurityOptions}}"], timeout=20)
        if info.rc == 0 and "rootless" in (info.stdout or "").lower():
            return SandboxStatus(True, "Docker rootless sandbox is ready", "docker")
        colima_profile = live_colima_docker(run_cmd, docker)
        if colima_profile:
            return SandboxStatus(True, f"Docker is isolated in Colima profile '{colima_profile}'", "docker")
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
        "set -eu; test -n \"$(find /source -mindepth 1 -maxdepth 1 -print -quit)\" || { echo 'Night Shift source mount is empty'; exit 125; }; "
        "rsync -a --exclude=node_modules /source/ /work/; "
        "if [ -d /deps/node_modules ]; then ln -s /deps/node_modules /work/node_modules; fi; "
        "cd /work; rm -rf .git; git init -q; "
        "git config user.email night-shift@localhost; git config user.name 'Night Shift'; "
        "git add -A; git commit -qm baseline; "
        "git apply --recount --whitespace=error /input/candidate.patch; git diff --check; "
        "git diff --name-only > /artifacts/changed-paths.txt; "
        "git diff --binary > /artifacts/applied.patch; set +e; \"$@\" > /artifacts/verification.txt 2>&1; "
        "rc=$?; printf '%s\\n' \"$rc\" > /artifacts/verification.rc; exit \"$rc\""
    )


def fixed_verify_script() -> str:
    """Copy read-only source into disposable tmpfs before running checks."""
    return (
        "set -eu; test -n \"$(find /source -mindepth 1 -maxdepth 1 -print -quit)\" || { echo 'Night Shift source mount is empty'; exit 125; }; "
        "rsync -a --exclude=node_modules /source/ /work/; "
        "if [ -d /deps/node_modules ]; then ln -s /deps/node_modules /work/node_modules; fi; "
        "cd /work; rm -rf .git; git init -q; "
        "git config user.email night-shift@localhost; git config user.name 'Night Shift'; "
        "git add -A; git commit -qm baseline; exec \"$@\""
    )


def dependency_volume(dependency_source: Path | None) -> list[str]:
    """Expose a repo's installed dependencies read-only inside the disposable worktree."""
    if dependency_source is None:
        return []
    if dependency_source.name != "node_modules" or dependency_source.is_symlink() or not dependency_source.is_dir():
        return []
    return ["--volume", f"{dependency_source.resolve()}:/deps/node_modules:ro"]


def dependency_cache_path(root: Path, remote: str, image: str, lockfile: Path) -> Path:
    """Return a cache path bound to the repo, runner image, and lockfile."""
    try:
        lock_digest = hashlib.sha256(lockfile.read_bytes()).hexdigest()
    except OSError:
        lock_digest = "missing-lockfile"
    key = hashlib.sha256(f"{remote}\0{image}\0{lock_digest}".encode("utf-8")).hexdigest()[:32]
    return root / key


def dependency_cache_ready(cache_dir: Path, remote: str, image: str, lockfile: Path) -> Path | None:
    """Accept only a cache created by Night Shift for this exact input set."""
    node_modules = cache_dir / "node_modules"
    marker = cache_dir / "READY.json"
    if cache_dir.is_symlink() or node_modules.is_symlink() or not node_modules.is_dir() or not marker.is_file():
        return None
    try:
        metadata = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    expected = dependency_cache_path(cache_dir.parent, remote, image, lockfile)
    if expected != cache_dir or metadata.get("remote") != remote or metadata.get("image") != image:
        return None
    try:
        if metadata.get("lock_digest") != hashlib.sha256(lockfile.read_bytes()).hexdigest():
            return None
    except OSError:
        return None
    return node_modules


def dependency_source_for_repo(
    repo: Path,
    cache_root: Path,
    remote: str,
    image: str,
) -> Path | None:
    """Prefer a runner-native cache, then fall back to a host dependency tree."""
    lockfile = repo / "package-lock.json"
    if remote and lockfile.is_file():
        prepared = dependency_cache_ready(
            dependency_cache_path(cache_root, remote, image, lockfile), remote, image, lockfile,
        )
        if prepared:
            return prepared
    host = repo / "node_modules"
    if host.is_dir() and not host.is_symlink():
        return host
    return None


def dependency_prepare_command(repo: Path, cache_dir: Path, image: str) -> list[str | Path]:
    """Build Linux/runner-native npm dependencies in a disposable networked setup container."""
    runtime = sandbox_runtime() or "docker"
    script = (
        "set -eu; rm -rf /deps/node_modules /deps/READY.json; "
        "rsync -a --exclude=node_modules --exclude=.git --exclude=.npmrc /source/ /work/; "
        "cd /work; npm ci --ignore-scripts --no-audit --no-fund; "
        "if [ -f prisma/schema.prisma ] && [ -x node_modules/.bin/prisma ]; then node_modules/.bin/prisma generate --schema prisma/schema.prisma; fi; "
        "mv /work/node_modules /deps/node_modules; test -d /deps/node_modules"
    )
    return [
        runtime, "run", "--rm", "--pull", "never", "--network", "bridge", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "256", "--cpus", "2", "--memory", "4096m",
        "--tmpfs", "/tmp:rw,exec,nosuid,size=512m,mode=1777",
        "--tmpfs", "/work:rw,exec,nosuid,size=4g,mode=700",
        "--volume", f"{cache_dir.resolve()}:/deps:rw",
        "--volume", f"{repo.resolve()}:/source:ro",
        "--workdir", "/work", "--env", "HOME=/tmp",
        "--env", "NPM_CONFIG_USERCONFIG=/dev/null",
        "--env", "NPM_CONFIG_CACHE=/work/.npm-cache",
        "--env", "NPM_CONFIG_IGNORE_SCRIPTS=true",
        image, "sh", "-ceu", script, "night-shift-prepare-dependencies",
    ]


def prepare_node_dependencies(
    repo: Path,
    cache_dir: Path,
    remote: str,
    image: str,
    run_cmd: Callable,
) -> tuple[bool, str]:
    """Prepare npm dependencies without touching the checkout or carrying host credentials."""
    lockfile = repo / "package-lock.json"
    if not lockfile.is_file() or not (repo / "package.json").is_file():
        return False, "runner-native dependency setup currently requires package.json and package-lock.json"
    if cache_dir.exists() and cache_dir.is_symlink():
        return False, "refusing to use a symlinked dependency cache"
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.chmod(0o700)
    except OSError as exc:
        return False, f"could not create the dependency cache: {exc}"
    result = run_cmd(dependency_prepare_command(repo, cache_dir, image), cwd=repo, timeout=1800)
    if result.rc != 0:
        detail = (result.stderr or result.stdout or f"dependency setup exited {result.rc}").strip()
        return False, detail[:600]
    try:
        marker = cache_dir / "READY.json"
        marker.write_text(
            json.dumps({
                "remote": remote,
                "image": image,
                "lock_digest": hashlib.sha256(lockfile.read_bytes()).hexdigest(),
                "prepared_at": int(time.time()),
            }, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        marker.chmod(0o600)
    except OSError as exc:
        return False, f"dependency setup completed but its readiness marker could not be saved: {exc}"
    return True, str(cache_dir / "node_modules")


def sandbox_patch_command(
    source: Path,
    patch: Path,
    artifacts: Path,
    command: tuple[str, ...],
    profile: RepoProfile,
    dependency_source: Path | None = None,
) -> list[str]:
    """Build the only writable-patch command Night Shift permits.

    Source and patch are read-only. The writable workspace lives only in the
    container tmpfs; the artifact directory receives logs and a candidate diff.
    """
    runtime = sandbox_runtime() or "docker"
    # Approved checks may compile and execute test binaries. The workspace is
    # disposable, no-network tmpfs; the host source remains mounted read-only.
    # The pinned image runs as UID 0 with every capability dropped. Let the
    # runtime give /work to that UID; forcing nobody:nogroup makes mode 700
    # inaccessible without CAP_DAC_OVERRIDE.
    tmpfs_options = "rw,exec,nosuid,size=512m,mode=700"
    return [
        runtime, "run", "--rm", "--pull", "never", "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", str(profile.max_pids), "--cpus", str(profile.max_cpu),
        "--memory", f"{profile.max_memory_mb}m", "--tmpfs", f"/work:{tmpfs_options}",
        "--tmpfs", "/tmp:rw,exec,nosuid,size=256m,mode=1777",
        *dependency_volume(dependency_source),
        "--volume", f"{source.resolve()}:/source:ro", "--volume", f"{patch.resolve()}:/input/candidate.patch:ro",
        "--volume", f"{artifacts.resolve()}:/artifacts:rw", "--workdir", "/work",
        "--env", "HOME=/tmp", "--env", "GIT_CONFIG_NOSYSTEM=1", profile.image,
        "sh", "-ceu", fixed_patch_script(), "night-shift-verify", *command,
    ]


def sandbox_command(
    repo: Path,
    command: tuple[str, ...],
    profile: RepoProfile,
    dependency_source: Path | None = None,
) -> list[str]:
    """Run with no host credentials/network and bounded resources.

    The repo mount is intentionally read-only. A future patch worker must write
    its patch to a separate, explicitly mounted artifact directory.
    """
    runtime = sandbox_runtime() or "docker"
    home = "/tmp"
    return [
        runtime, "run", "--rm", "--pull", "never", "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", str(profile.max_pids), "--cpus", str(profile.max_cpu),
        "--memory", f"{profile.max_memory_mb}m", "--tmpfs", f"{home}:rw,exec,nosuid,size=256m,mode=1777",
        "--tmpfs", "/work:rw,exec,nosuid,size=512m,mode=700", "--workdir", "/work",
        *dependency_volume(dependency_source),
        "--volume", f"{repo.resolve()}:/source:ro",
        "--env", f"HOME={home}", "--env", "GIT_CONFIG_NOSYSTEM=1",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        profile.image, "sh", "-ceu", fixed_verify_script(), "night-shift-verify", *command,
    ]
