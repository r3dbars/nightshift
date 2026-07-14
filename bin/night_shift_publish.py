"""Fail-closed publication of independently verified Night Shift patches."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Callable

from night_shift_patch_protocol import validate_patch
from night_shift_policy import RepoProfile
from night_shift_sandbox import sandbox_command


PUBLISHABLE_STATUSES = {"PROVEN_REPAIR", "VERIFIED_DRAFT"}
HOSTED_CHECK_FAILURES = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"}
HOSTED_CHECK_PENDING = {"", "EXPECTED", "PENDING", "QUEUED", "IN_PROGRESS", "WAITING", "REQUESTED"}


def summarize_hosted_checks(checks: list[dict]) -> dict:
    """Summarize GitHub check runs without treating missing data as a pass."""
    names: list[str] = []
    failed: list[str] = []
    pending: list[str] = []
    unknown: list[str] = []
    for check in checks:
        if not isinstance(check, dict):
            unknown.append("unknown")
            continue
        name = str(check.get("name") or check.get("context") or "unknown")
        state = str(check.get("conclusion") or check.get("state") or check.get("status") or "").upper()
        names.append(name)
        if state in HOSTED_CHECK_FAILURES:
            failed.append(name)
        elif state in HOSTED_CHECK_PENDING:
            pending.append(name)
        elif state != "SUCCESS":
            unknown.append(name)
    if failed:
        status = "failed"
    elif pending:
        status = "pending"
    elif unknown or not checks:
        status = "unknown"
    else:
        status = "passed"
    return {
        "state": status,
        "check_count": len(checks),
        "checks": names,
        "failed": failed,
        "pending": pending,
        "unknown": unknown,
    }


class PublishEngine:
    def __init__(
        self,
        run_cmd: Callable,
        worktree_root: Path,
        now_stamp: Callable[[], str],
        publication_ledger: Path | None = None,
        sleep: Callable[[float], None] = time.sleep,
        hosted_check_attempts: int = 3,
        hosted_check_interval: float = 5.0,
    ) -> None:
        self.run_cmd = run_cmd
        self.worktree_root = worktree_root
        self.now_stamp = now_stamp
        self.publication_ledger = publication_ledger or worktree_root.parent / "published-drafts.jsonl"
        self.sleep = sleep
        self.hosted_check_attempts = max(1, hosted_check_attempts)
        self.hosted_check_interval = max(0.0, hosted_check_interval)

    def _poll_hosted_checks(self, worktree: Path, pr_url: str) -> dict:
        """Poll briefly, then preserve pending/unknown as explicit morning evidence."""
        latest = {"state": "unknown", "check_count": 0, "checks": [], "failed": [], "pending": [], "unknown": []}
        for attempt in range(self.hosted_check_attempts):
            viewed = self.run_cmd(
                ["gh", "pr", "view", pr_url, "--json", "statusCheckRollup"],
                cwd=worktree,
                timeout=30,
            )
            try:
                payload = json.loads(viewed.stdout)
                if not isinstance(payload, dict):
                    raise ValueError("GitHub returned a non-object response")
                checks = payload.get("statusCheckRollup")
                if not isinstance(checks, list):
                    raise ValueError("statusCheckRollup is not a list")
                latest = summarize_hosted_checks(checks)
            except (TypeError, ValueError, json.JSONDecodeError):
                latest = {
                    "state": "unknown",
                    "check_count": 0,
                    "checks": [],
                    "failed": [],
                    "pending": [],
                    "unknown": [],
                    "reason": "GitHub check status could not be read",
                }
            latest["observed_at"] = self.now_stamp()
            if latest["state"] != "pending" or attempt + 1 >= self.hosted_check_attempts:
                return latest
            self.sleep(self.hosted_check_interval)
        return latest

    def _already_published(self, fingerprint: str) -> bool:
        try:
            rows = self.publication_ledger.read_text(encoding="utf-8").splitlines()
        except OSError:
            return False
        for line in rows:
            try:
                if json.loads(line).get("fingerprint") == fingerprint:
                    return True
            except (TypeError, ValueError):
                continue
        return False

    def _record_publication(self, fingerprint: str, repo_name: str, pr_url: str, branch: str) -> None:
        self.publication_ledger.parent.mkdir(parents=True, exist_ok=True)
        with self.publication_ledger.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "status": "DRAFT_PR_OPENED",
                "fingerprint": fingerprint,
                "repo": repo_name,
                "pr_url": pr_url,
                "branch": branch,
            }, sort_keys=True) + "\n")

    def reconcile_drafts(self, repo: Path) -> list[dict]:
        """Refresh hosted status for recorded draft PRs using read-only GitHub calls."""
        try:
            lines = self.publication_ledger.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        rows: list[dict] = []
        for line in lines:
            try:
                row = json.loads(line)
            except (TypeError, ValueError, json.JSONDecodeError):
                return []
            if not isinstance(row, dict):
                return []
            rows.append(row)

        changed = False
        for row in rows:
            if row.get("status") != "DRAFT_PR_OPENED" or not row.get("pr_url"):
                continue
            viewed = self.run_cmd(
                ["gh", "pr", "view", str(row["pr_url"]), "--json", "isDraft,statusCheckRollup"],
                cwd=repo,
                timeout=30,
            )
            draft_state = "unknown"
            if viewed.rc != 0:
                hosted = {
                    "state": "unknown", "check_count": 0, "checks": [],
                    "failed": [], "pending": [], "unknown": [],
                    "reason": "GitHub draft status could not be read",
                }
            else:
                try:
                    payload = json.loads(viewed.stdout)
                    if not isinstance(payload, dict) or not isinstance(payload.get("statusCheckRollup"), list):
                        raise ValueError("statusCheckRollup is not a list")
                    hosted = summarize_hosted_checks(payload["statusCheckRollup"])
                    if payload.get("isDraft") is True:
                        draft_state = "draft"
                    elif payload.get("isDraft") is False:
                        draft_state = "not-draft"
                except (TypeError, ValueError, json.JSONDecodeError):
                    hosted = {
                        "state": "unknown", "check_count": 0, "checks": [],
                        "failed": [], "pending": [], "unknown": [],
                        "reason": "GitHub draft status returned an invalid response",
                    }
            observed_at = self.now_stamp()
            hosted["observed_at"] = observed_at
            row["hosted_checks"] = hosted
            row["draft_state"] = draft_state
            row["last_reconciled_at"] = observed_at
            changed = True

        if changed:
            self.publication_ledger.parent.mkdir(parents=True, exist_ok=True)
            content = "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"
            descriptor, temporary = tempfile.mkstemp(
                prefix=f".{self.publication_ledger.name}.",
                dir=self.publication_ledger.parent,
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self.publication_ledger)
            except Exception:
                try:
                    os.unlink(temporary)
                except OSError:
                    pass
                raise
        return rows

    def _cleanup(self, repo: Path, worktree: Path) -> bool:
        removed = self.run_cmd(["git", "worktree", "remove", "--force", worktree], cwd=repo, timeout=120)
        self.run_cmd(["git", "worktree", "prune"], cwd=repo, timeout=60)
        return removed.rc == 0

    def _remote_branch_sha(self, worktree: Path, branch: str) -> tuple[str, str]:
        ref = f"refs/heads/{branch}"
        present = self.run_cmd(["git", "ls-remote", "--exit-code", "--heads", "origin", ref], cwd=worktree, timeout=60)
        if present.rc == 2 or (present.rc == 0 and not present.stdout.strip()):
            return "absent", ""
        if present.rc != 0:
            return "unknown", ""
        return "present", present.stdout.split()[0]

    def _cleanup_owned_remote_branch(self, worktree: Path, branch: str, expected_sha: str) -> str:
        state, remote_sha = self._remote_branch_sha(worktree, branch)
        if state == "absent":
            return "absent"
        if state != "present":
            return "unknown"
        if remote_sha != expected_sha:
            return "foreign"
        removed = self.run_cmd(["git", "push", "origin", "--delete", branch], cwd=worktree, timeout=120)
        if removed.rc != 0:
            return "unknown"
        checked, _ = self._remote_branch_sha(worktree, branch)
        return "removed" if checked == "absent" else "unknown"

    def _find_pr(
        self, worktree: Path, repo_name: str, branch: str, state: str = "open"
    ) -> tuple[str, str]:
        found = self.run_cmd(
            ["gh", "pr", "list", "--repo", repo_name, "--head", branch, "--state", state, "--json", "url", "--limit", "1"],
            cwd=worktree,
            timeout=60,
        )
        if found.rc != 0:
            return "unknown", ""
        try:
            rows = json.loads(found.stdout)
        except (TypeError, ValueError):
            return "unknown", ""
        if not rows:
            return "absent", ""
        url = str(rows[0].get("url") or "")
        return ("present", url) if url else ("unknown", "")

    def _find_patch_pr_history(
        self, worktree: Path, repo_name: str, branch: str, fingerprint: str
    ) -> tuple[str, str]:
        found = self.run_cmd(
            [
                "gh", "pr", "list", "--repo", repo_name, "--state", "all",
                "--json", "url,headRefName", "--limit", "100",
            ],
            cwd=worktree,
            timeout=60,
        )
        if found.rc != 0:
            return "unknown", ""
        try:
            rows = json.loads(found.stdout)
        except (TypeError, ValueError):
            return "unknown", ""
        old_suffix = f"-{fingerprint}"
        for row in rows:
            head = str(row.get("headRefName") or "")
            if head == branch or (head.startswith("night-shift/") and head.endswith(old_suffix)):
                url = str(row.get("url") or "")
                return ("present", url) if url else ("unknown", "")
        return "absent", ""

    def publish(
        self,
        repo: Path,
        repo_name: str,
        proof: dict,
        profile: RepoProfile,
        proof_dir: Path,
        dependency_source: Path | None = None,
    ) -> dict:
        proof_dir.mkdir(parents=True, exist_ok=True)
        result_path = proof_dir / "publish.json"

        def finish(result: dict) -> dict:
            result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return result

        if proof.get("status") not in PUBLISHABLE_STATUSES:
            return finish({"status": "REJECT", "reason": "patch lacks verified draft proof"})
        if not profile.may_execute or profile.trust != "owned":
            return finish({"status": "REJECT", "reason": "repo profile is not approved for owned sandbox execution"})
        source_ref = str(proof.get("source_ref") or "")
        patch_path = Path(str(proof.get("patch") or ""))
        allowed_files = [str(path) for path in proof.get("files") or []]
        verification_argv = tuple(proof.get("verification_argv") or ())
        if not re.fullmatch(r"[0-9a-f]{40}", source_ref):
            return finish({"status": "REJECT", "reason": "publication requires an exact 40-character source SHA"})
        if not patch_path.is_file() or not allowed_files or verification_argv not in profile.commands:
            return finish({"status": "REJECT", "reason": "proof is missing its validated patch, files, or approved verification"})
        patch = patch_path.read_text(encoding="utf-8")
        validated = validate_patch(patch, allowed_files, profile)
        if not validated.valid:
            return finish({"status": "REJECT", "reason": "; ".join(validated.reasons)})

        who = self.run_cmd(["gh", "api", "user", "--jq", ".login"], cwd=repo, timeout=30)
        view = self.run_cmd(
            ["gh", "repo", "view", "--json", "nameWithOwner,isFork,defaultBranchRef"],
            cwd=repo,
            timeout=30,
        )
        try:
            metadata = json.loads(view.stdout)
        except (TypeError, ValueError):
            metadata = {}
        owner = str(metadata.get("nameWithOwner") or "").split("/", 1)[0]
        default_branch = str((metadata.get("defaultBranchRef") or {}).get("name") or "")
        if (
            who.rc != 0
            or view.rc != 0
            or str(metadata.get("nameWithOwner") or "").casefold() != repo_name.casefold()
            or who.stdout.strip().casefold() != owner.casefold()
            or metadata.get("isFork")
            or not default_branch
        ):
            return finish({"status": "REJECT", "reason": "authenticated GitHub user must own this non-fork repository"})

        default_ref = f"origin/{default_branch}"
        default_exists = self.run_cmd(["git", "rev-parse", "--verify", default_ref], cwd=repo, timeout=30)
        ancestry = self.run_cmd(["git", "merge-base", "--is-ancestor", source_ref, default_ref], cwd=repo, timeout=30)
        if default_exists.rc != 0 or ancestry.rc != 0:
            return finish({
                "status": "REJECT",
                "reason": "source commit is not on the fetched default branch; PR-head repairs stay local",
            })

        fingerprint = hashlib.sha256((repo_name + source_ref + patch).encode("utf-8")).hexdigest()[:12]
        if self._already_published(fingerprint):
            return finish({"status": "REJECT", "reason": "this exact verified patch was already published"})
        branch = f"night-shift/{fingerprint}"
        prior_pr_state, prior_pr_url = self._find_patch_pr_history(
            repo, repo_name, branch, fingerprint
        )
        if prior_pr_state == "present":
            return finish({
                "status": "REJECT",
                "reason": "this exact verified patch already has GitHub PR history",
                "pr_url": prior_pr_url,
            })
        if prior_pr_state != "absent":
            return finish({
                "status": "REJECT",
                "reason": "could not prove this verified patch has no prior GitHub PR",
            })
        worktree = self.worktree_root / re.sub(r"[^A-Za-z0-9._-]+", "--", repo_name) / branch.replace("/", "-")
        worktree.parent.mkdir(parents=True, exist_ok=True)
        added = self.run_cmd(["git", "worktree", "add", "--detach", worktree, source_ref], cwd=repo, timeout=120)
        if added.rc != 0:
            return finish({"status": "REJECT", "reason": "could not create pinned publication worktree"})

        pushed = False
        pr_url = ""
        try:
            checked = self.run_cmd(["git", "apply", "--check", patch_path], cwd=worktree, timeout=30)
            applied = self.run_cmd(["git", "apply", patch_path], cwd=worktree, timeout=30) if checked.rc == 0 else checked
            if applied.rc != 0:
                return finish({"status": "REJECT", "reason": "validated patch no longer applies to its pinned source"})
            changed = self.run_cmd(["git", "diff", "--name-only"], cwd=worktree, timeout=30)
            paths = [line for line in changed.stdout.splitlines() if line]
            if set(paths) != set(validated.paths):
                return finish({"status": "REJECT", "reason": "fresh worktree changed a different file set"})
            verified = self.run_cmd(
                sandbox_command(worktree, verification_argv, profile, dependency_source or repo / "node_modules"),
                cwd=worktree,
                timeout=profile.max_seconds,
            )
            (proof_dir / "publish-verification.txt").write_text(
                (verified.stdout + "\n" + verified.stderr).strip() + "\n", encoding="utf-8"
            )
            if verified.rc != 0:
                return finish({"status": "REJECT", "reason": "fresh publication verification failed"})
            staged = self.run_cmd(["git", "add", "--", *validated.paths], cwd=worktree, timeout=30)
            committed = self.run_cmd(
                [
                    "git", "-c", "user.name=Night Shift", "-c",
                    "user.email=night-shift@users.noreply.github.com",
                    "-c", "commit.gpgSign=false",
                    "commit", "-m", f"Night Shift: {str(proof.get('summary') or 'verified repair')[:60]}",
                ],
                cwd=worktree,
                timeout=60,
            ) if staged.rc == 0 else staged
            if committed.rc != 0:
                return finish({"status": "REJECT", "reason": "could not commit the approved patch"})
            local_commit = self.run_cmd(["git", "rev-parse", "HEAD"], cwd=worktree, timeout=30)
            if local_commit.rc != 0 or not re.fullmatch(r"[0-9a-f]{40}", local_commit.stdout.strip()):
                return finish({"status": "REJECT", "reason": "could not pin the publication commit"})
            local_sha = local_commit.stdout.strip()
            branch_state, _ = self._remote_branch_sha(worktree, branch)
            if branch_state != "absent":
                return finish({
                    "status": "REJECT",
                    "reason": "draft branch name is already in use" if branch_state == "present" else "could not prove the draft branch name is unused",
                })
            pushed_result = self.run_cmd(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], cwd=worktree, timeout=120)
            if pushed_result.rc != 0:
                cleanup = self._cleanup_owned_remote_branch(worktree, branch, local_sha)
                pushed = cleanup == "unknown"
                return finish({
                    "status": "REMOTE_CLEANUP_REQUIRED" if cleanup == "unknown" else "REJECT",
                    "reason": "push failed ambiguously and remote branch absence could not be proven" if cleanup == "unknown" else "unique draft branch push failed",
                    "remote_branch_created": pushed,
                })
            pushed = True
            title = f"Night Shift: {str(proof.get('summary') or 'verified repair')[:72]}"
            body = (
                "Night Shift prepared this small change in isolation.\n\n"
                f"Proof: {proof.get('proof_level', 'verified')}\n"
                f"Verification: `{' '.join(verification_argv)}`\n"
                f"Files: {', '.join(validated.paths)}\n\n"
                "This is a draft for human or cloud-agent review. Night Shift never merges it."
            )
            created = self.run_cmd(
                ["gh", "pr", "create", "--repo", repo_name, "--draft", "--head", branch, "--title", title, "--body", body],
                cwd=worktree,
                timeout=120,
            )
            pr_url = created.stdout.strip().splitlines()[-1] if created.rc == 0 and created.stdout.strip() else ""
            if created.rc != 0 or not pr_url:
                pr_state, recovered_url = self._find_pr(worktree, repo_name, branch)
                if pr_state == "present":
                    pr_url = recovered_url
                else:
                    cleanup = self._cleanup_owned_remote_branch(worktree, branch, local_sha)
                    removed_remote = cleanup in {"absent", "removed"}
                    pushed = not removed_remote
                    uncertain = pr_state == "unknown" or not removed_remote
                    return finish({
                        "status": "REMOTE_CLEANUP_REQUIRED" if uncertain else "REJECT",
                        "reason": "draft PR creation outcome could not be proven" if uncertain else "GitHub did not create the draft PR",
                        "remote_branch_created": pushed,
                    })
            draft = self.run_cmd(["gh", "pr", "view", pr_url, "--json", "isDraft", "--jq", ".isDraft"], cwd=worktree, timeout=30)
            if draft.rc != 0 or draft.stdout.strip().lower() != "true":
                closed = self.run_cmd(["gh", "pr", "close", pr_url], cwd=worktree, timeout=60)
                cleanup = self._cleanup_owned_remote_branch(worktree, branch, local_sha)
                removed_remote = cleanup in {"absent", "removed"}
                pushed = not removed_remote
                cleaned = closed.rc == 0 and removed_remote
                return finish({
                    "status": "REJECT" if cleaned else "REMOTE_CLEANUP_REQUIRED",
                    "reason": "GitHub did not preserve draft status" if cleaned else "non-draft PR or remote branch may still need manual cleanup",
                    "pr_url": pr_url,
                    "remote_branch_created": pushed,
                    "pr_closed": closed.rc == 0,
                })
            self._record_publication(fingerprint, repo_name, pr_url, branch)
            hosted_checks = self._poll_hosted_checks(worktree, pr_url)
            return finish({
                "status": "DRAFT_PR_OPENED",
                "fingerprint": fingerprint,
                "pr_url": pr_url,
                "branch": branch,
                "source_ref": source_ref,
                "files": list(validated.paths),
                "verification": " ".join(verification_argv),
                "hosted_checks": hosted_checks,
                "proof": str(result_path),
            })
        finally:
            removed = self._cleanup(repo, worktree)
            if result_path.exists():
                saved = json.loads(result_path.read_text(encoding="utf-8"))
                saved["worktree_removed"] = removed
                saved["remote_branch_created"] = pushed
                result_path.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n", encoding="utf-8")
