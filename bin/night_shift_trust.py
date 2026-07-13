"""External repo approvals that never modify the target checkout."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Callable

from night_shift_policy import RepoProfile, load_repo_profile, parse_repo_profile


def approval_path(root: Path, remote: str) -> Path:
    key = hashlib.sha256(remote.strip().encode("utf-8")).hexdigest()[:24]
    return root / f"{key}.json"


def load_effective_profile(
    repo: Path,
    approvals_root: Path,
    remote_reader: Callable[[Path], str],
    remote_revision_verifier: Callable[[Path, str], bool],
) -> tuple[RepoProfile | None, str]:
    local, detail = load_repo_profile(repo)
    if local is not None:
        return local, detail
    remote = remote_reader(repo).strip()
    if not remote:
        return None, detail
    path = approval_path(approvals_root, remote)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None, detail
    if record.get("remote") != remote or not isinstance(record.get("profile"), dict):
        return None, "saved repo approval does not match the current Git remote"
    if not remote_revision_verifier(repo, remote):
        return None, "current repo revision is not advertised by the approved Git remote"
    profile, parsed_detail = parse_repo_profile(record["profile"])
    if profile is None:
        return None, f"saved repo approval is invalid: {parsed_detail}"
    return replace(profile, external_approval=True, approved_remote=remote), "external repo approval loaded"


def save_approval(root: Path, remote: str, slug: str, profile: dict) -> Path:
    if root.is_symlink():
        raise OSError("refusing to use a symlinked repo approval directory")
    root.mkdir(parents=True, exist_ok=True)
    root.chmod(0o700)
    path = approval_path(root, remote)
    if path.is_symlink():
        raise OSError("refusing to replace a symlinked repo approval")
    body = json.dumps({"remote": remote, "slug": slug, "profile": profile}, indent=2, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=".approval-", dir=root)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
    return path
