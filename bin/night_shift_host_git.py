"""Host-side Git guardrails for disposable Night Shift checkouts."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable


_SAFE_GIT_CONFIG = (
    ("core.hooksPath", "/dev/null"),
    ("protocol.ext.allow", "never"),
    ("protocol.file.allow", "never"),
    ("submodule.recurse", "false"),
    ("credential.interactive", "never"),
)
_DANGEROUS_CONFIG = re.compile(
    r"^(?:filter\..*\.(?:clean|smudge|process|required)|diff\..*\.(?:command|textconv)|"
    r"core\.hooksPath|url\..*\.insteadOf)\b",
    re.IGNORECASE,
)
_DANGEROUS_ATTRIBUTE = re.compile(r"(?:^|\s)(?:filter|diff)=[^\s]+", re.IGNORECASE)
_EXTERNAL_CI_PATHS = {
    ".travis.yml",
    "Jenkinsfile",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
}


def safe_git_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """Inject command-scope Git policy while preserving the user's auth helper."""
    env = dict(os.environ if base is None else base)
    env["GIT_CONFIG_COUNT"] = str(len(_SAFE_GIT_CONFIG))
    for index, (key, value) in enumerate(_SAFE_GIT_CONFIG):
        env[f"GIT_CONFIG_KEY_{index}"] = key
        env[f"GIT_CONFIG_VALUE_{index}"] = value
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def checkout_safety_reasons(
    run_cmd: Callable,
    repo: Path,
    source_ref: str,
) -> list[str]:
    """Reject local Git execution surfaces before creating a host worktree."""
    reasons: list[str] = []
    configured = run_cmd(
        ["git", "config", "--local", "--get-regexp", ".*"],
        cwd=repo,
        timeout=20,
        env=safe_git_env(),
    )
    if configured.rc == 0:
        for line in configured.stdout.splitlines():
            key = line.split(None, 1)[0] if line.strip() else ""
            if _DANGEROUS_CONFIG.search(key):
                reasons.append(f"repo Git config defines an executable driver: {key}")

    listed = run_cmd(
        ["git", "ls-tree", "-r", "--name-only", source_ref],
        cwd=repo,
        timeout=30,
        env=safe_git_env(),
    )
    if listed.rc != 0:
        reasons.append("could not inspect the pinned tree for Git attributes")
        return reasons
    attribute_paths = [
        path for path in listed.stdout.splitlines()
        if Path(path).name == ".gitattributes"
    ][:50]
    for relative in attribute_paths:
        shown = run_cmd(
            ["git", "show", f"{source_ref}:{relative}"],
            cwd=repo,
            timeout=20,
            env=safe_git_env(),
        )
        if shown.rc != 0 or _DANGEROUS_ATTRIBUTE.search(shown.stdout):
            reasons.append(f"pinned tree has an executable Git attribute: {relative}")
    return list(dict.fromkeys(reasons))


def publication_ci_reasons(run_cmd: Callable, repo: Path, source_ref: str) -> list[str]:
    """Block same-repo draft publication when CI cannot be reliably suppressed."""
    listed = run_cmd(
        ["git", "ls-tree", "-r", "--name-only", source_ref],
        cwd=repo,
        timeout=30,
        env=safe_git_env(),
    )
    if listed.rc != 0:
        return ["could not inspect CI configuration before publication"]
    paths = set(listed.stdout.splitlines())
    reasons: list[str] = []
    if any(path in _EXTERNAL_CI_PATHS or path.startswith((".circleci/", ".buildkite/")) for path in paths):
        reasons.append("external CI configuration may run a same-repo branch")
    for relative in sorted(path for path in paths if path.startswith(".github/workflows/")):
        shown = run_cmd(
            ["git", "show", f"{source_ref}:{relative}"],
            cwd=repo,
            timeout=20,
            env=safe_git_env(),
        )
        if shown.rc != 0:
            reasons.append(f"could not inspect workflow before publication: {relative}")
        elif re.search(r"(?m)^\s*pull_request_target\s*:", shown.stdout):
            reasons.append(f"workflow uses pull_request_target: {relative}")
    return list(dict.fromkeys(reasons))
