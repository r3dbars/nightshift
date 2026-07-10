from __future__ import annotations

import json
import os
import re
import shutil
import textwrap
import time
from pathlib import Path
from typing import Callable

from night_shift_policy import RepoProfile, path_is_allowed, path_is_protected
from night_shift_sandbox import sandbox_command


def draft_proof_status(baseline_rc: int, after_rc: int, guards: list[str]) -> tuple[str, str]:
    if guards:
        return "REJECT", "not proven"
    if baseline_rc != 0 and after_rc == 0:
        return "PROVEN_REPAIR", "failing-before and passing-after"
    return "VERIFIED_DRAFT", "passing repository check after a bounded patch"


def remaining_draft_timeout(
    timeout: int,
    deadline: float | None = None,
    stop_file: Path | None = None,
) -> int:
    if stop_file and stop_file.exists():
        return 0
    if deadline is None:
        return max(1, timeout)
    return max(0, min(timeout, int(deadline - time.time())))


class DraftEngine:
    def __init__(self, run_cmd: Callable, worktree_root: Path, now_stamp: Callable[[], str]) -> None:
        self.run_cmd = run_cmd
        self.worktree_root = worktree_root
        self.now_stamp = now_stamp

    def select_candidate(
        self,
        child_ledger: Path,
        repo: Path,
        repo_signal_scan: Callable[[Path], dict],
        task_ladder: dict[str, int],
    ) -> dict | None:
        try:
            items = json.loads((child_ledger / "work-queue.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        default_commands = repo_signal_scan(repo).get("test_commands") or []
        items.sort(key=lambda item: (-task_ladder.get(item.get("ladder", "strengthen"), 0), item.get("rank", 999)))
        for item in items:
            if not item.get("executable") or item.get("proof_kind") != "test":
                continue
            if item.get("score") not in {"KEEP", "MAYBE"}:
                continue
            if item.get("action_type") not in {"patch-plan", "draft-pr-candidate"}:
                continue
            source_ref = str(item.get("source_ref") or "")
            if source_ref:
                files = [
                    path
                    for path in item.get("files") or []
                    if self.run_cmd(["git", "cat-file", "-e", f"{source_ref}:{path}"], cwd=repo, timeout=20).rc == 0
                ]
            else:
                files = [path for path in item.get("files") or [] if (repo / path).is_file()]
            known_commands = item.get("verification_commands") or default_commands
            verification = next((command for command in known_commands if command in (item.get("tests") or "")), "")
            if files and verification:
                return {**item, "files": files[:6], "verification": verification}
        return None

    def guard_reasons(
        self, worktree: Path, allowed_files: list[str], profile: RepoProfile | None = None
    ) -> list[str]:
        changed = self.run_cmd(["git", "diff", "--name-only"], cwd=worktree, timeout=30)
        paths = [line.strip() for line in changed.stdout.splitlines() if line.strip()]
        reasons: list[str] = []
        if not paths:
            return ["no patch was produced"]
        if len(paths) > 6:
            reasons.append("patch touched more than 6 files")
        if any(path not in set(allowed_files) for path in paths):
            reasons.append("patch touched a file outside the approved candidate set")
        if profile and any(path_is_protected(path, profile.protected_paths) for path in paths):
            reasons.append("patch touched an immutable verifier, dependency, or policy file")
        if profile and any(not path_is_allowed(path, profile.allowed_paths) for path in paths):
            reasons.append("patch touched a path outside the repo profile allowlist")
        forbidden_names = {
            ".env",
            ".env.local",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "poetry.lock",
            "Cargo.lock",
        }
        if any(Path(path).name in forbidden_names for path in paths):
            reasons.append("patch changed a credential or dependency lock file")
        stats = self.run_cmd(["git", "diff", "--numstat"], cwd=worktree, timeout=30)
        changed_lines = 0
        for line in stats.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                changed_lines += int(parts[0]) + int(parts[1])
        if changed_lines > 500:
            reasons.append("patch exceeded the 500-line overnight limit")
        diff = self.run_cmd(["git", "diff", "--unified=0"], cwd=worktree, timeout=30).stdout
        additions = "\n".join(line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
        if re.search(r"(?i)(api[_-]?key|secret|password|private[_-]?key)\s*[:=]\s*['\"][^'\"]+", additions):
            reasons.append("patch appears to add a secret")
        if re.search(r"(?i)\b(merge|release|publish|deploy|notarize|appcast|cask)\b", additions):
            reasons.append("patch adds a forbidden release or deployment action")
        if re.search(
            r"(?i)(allowlist|allow_list|ignore|skip|disable).{0,80}(check|test|lint|security|policy)|"
            r"(check|test|lint|security|policy).{0,80}(allowlist|allow_list|ignore|skip|disable)",
            additions,
        ):
            reasons.append("patch appears to bypass a test, check, or security policy")
        return reasons

    def cleanup(self, repo: Path, worktree: Path) -> bool:
        removed = self.run_cmd(["git", "worktree", "remove", "--force", worktree], cwd=repo, timeout=120)
        self.run_cmd(["git", "worktree", "prune"], cwd=repo, timeout=60)
        return removed.rc == 0

    def run_draft(
        self,
        repo: Path,
        repo_name: str,
        candidate: dict,
        parent_ledger: Path,
        timeout: int,
        windows_url: str,
        windows_model: str,
        deadline: float | None = None,
        stop_file: Path | None = None,
        profile: RepoProfile | None = None,
    ) -> dict:
        safe_repo = re.sub(r"[^A-Za-z0-9._-]+", "--", repo_name)
        safe_task = re.sub(r"[^A-Za-z0-9._-]+", "-", candidate.get("key", "draft"))[:80]
        worktree = self.worktree_root / safe_repo / f"{self.now_stamp()}-{safe_task}"
        proof_dir = parent_ledger / "drafts" / safe_repo
        proof_dir.mkdir(parents=True, exist_ok=True)
        proof_path = proof_dir / f"{safe_task}.json"
        patch_path = proof_dir / f"{safe_task}.patch"
        initial_timeout = remaining_draft_timeout(timeout, deadline, stop_file)
        if initial_timeout <= 0:
            result = {"status": "REJECT", "reason": "stop limit reached before draft execution"}
            proof_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return result
        if profile is None:
            result = {"status": "REJECT", "reason": "missing trusted repo profile", "proof_level": "not executed"}
            proof_path.parent.mkdir(parents=True, exist_ok=True)
            proof_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return result
        worktree.parent.mkdir(parents=True, exist_ok=True)
        source_ref = str(candidate.get("source_ref") or "HEAD")
        added = self.run_cmd(
            ["git", "worktree", "add", "--detach", worktree, source_ref],
            cwd=repo,
            timeout=min(initial_timeout, 120),
            pid_log=parent_ledger / "processes.tsv",
        )
        if added.rc != 0:
            removed = self.cleanup(repo, worktree) if worktree.exists() else True
            result = {
                "status": "REJECT",
                "reason": (added.stderr or added.stdout)[:300],
                "worktree": str(worktree),
                "source_ref": source_ref,
                "worktree_removed": removed,
            }
            proof_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return result

        def finish(result: dict) -> dict:
            result["worktree_removed"] = self.cleanup(repo, worktree)
            proof_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return result

        verification_argv = tuple(candidate.get("verification_argv") or ())
        if verification_argv not in profile.commands:
            return finish({"status": "REJECT", "reason": "verification is not approved by the repo profile"})
        verification = " ".join(verification_argv)
        baseline_timeout = remaining_draft_timeout(timeout, deadline, stop_file)
        if baseline_timeout <= 0:
            return finish({"status": "REJECT", "reason": "stop limit reached before baseline verification"})
        baseline = self.run_cmd(
            sandbox_command(worktree, verification_argv, profile),
            cwd=worktree,
            timeout=min(baseline_timeout, profile.max_seconds),
            pid_log=parent_ledger / "processes.tsv",
        )
        (proof_dir / f"{safe_task}.baseline.txt").write_text(
            (baseline.stdout + "\n" + baseline.stderr).strip() + "\n",
            encoding="utf-8",
        )
        baseline_dirty = self.run_cmd(["git", "status", "--porcelain"], cwd=worktree, timeout=30)
        if baseline_dirty.stdout.strip():
            return finish(
                {
                    "status": "REJECT",
                    "reason": "baseline verification modified the disposable worktree",
                    "worktree": str(worktree),
                    "baseline_rc": baseline.rc,
                }
            )
        # A model worker would need its own writable container and a separate
        # patch-output mount. Do not fall back to a host worktree while that
        # boundary is unavailable.
        if not windows_url or not windows_model:
            return finish(
                {
                    "status": "REJECT",
                    "reason": "sandboxed coding lane is not configured",
                    "worktree": str(worktree),
                    "baseline_rc": baseline.rc,
                }
            )
        return finish({
            "status": "REJECT",
            "reason": "baseline ran in the sandbox; writable patch workers are intentionally disabled until the isolated patch protocol is installed",
            "repo": repo_name,
            "source_ref": source_ref,
            "verification": verification,
            "baseline_rc": baseline.rc,
            "proof_level": "reproduced only" if baseline.rc != 0 else "baseline clean",
        })
