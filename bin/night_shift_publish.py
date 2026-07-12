"""Fail-closed publication of independently verified Night Shift patches."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable

from night_shift_patch_protocol import validate_patch
from night_shift_policy import RepoProfile
from night_shift_sandbox import sandbox_command


PUBLISHABLE_STATUSES = {"PROVEN_REPAIR", "VERIFIED_DRAFT"}


class PublishEngine:
    def __init__(
        self,
        run_cmd: Callable,
        worktree_root: Path,
        now_stamp: Callable[[], str],
        publication_ledger: Path | None = None,
    ) -> None:
        self.run_cmd = run_cmd
        self.worktree_root = worktree_root
        self.now_stamp = now_stamp
        self.publication_ledger = publication_ledger or worktree_root.parent / "published-drafts.jsonl"

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
                "fingerprint": fingerprint,
                "repo": repo_name,
                "pr_url": pr_url,
                "branch": branch,
            }, sort_keys=True) + "\n")

    def _cleanup(self, repo: Path, worktree: Path) -> bool:
        removed = self.run_cmd(["git", "worktree", "remove", "--force", worktree], cwd=repo, timeout=120)
        self.run_cmd(["git", "worktree", "prune"], cwd=repo, timeout=60)
        return removed.rc == 0

    def _remove_remote_branch(self, worktree: Path, branch: str) -> None:
        self.run_cmd(["git", "push", "origin", "--delete", branch], cwd=worktree, timeout=120)

    def publish(
        self,
        repo: Path,
        repo_name: str,
        proof: dict,
        profile: RepoProfile,
        proof_dir: Path,
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
        if (
            who.rc != 0
            or view.rc != 0
            or str(metadata.get("nameWithOwner") or "").casefold() != repo_name.casefold()
            or who.stdout.strip().casefold() != owner.casefold()
            or metadata.get("isFork")
        ):
            return finish({"status": "REJECT", "reason": "authenticated GitHub user must own this non-fork repository"})

        fingerprint = hashlib.sha256((repo_name + source_ref + patch).encode("utf-8")).hexdigest()[:12]
        if self._already_published(fingerprint):
            return finish({"status": "REJECT", "reason": "this exact verified patch was already published"})
        branch = f"night-shift/{self.now_stamp().lower()}-{fingerprint}"
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
                sandbox_command(worktree, verification_argv, profile),
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
                ["git", "commit", "-m", f"Night Shift: {str(proof.get('summary') or 'verified repair')[:60]}"],
                cwd=worktree,
                timeout=60,
            ) if staged.rc == 0 else staged
            if committed.rc != 0:
                return finish({"status": "REJECT", "reason": "could not commit the approved patch"})
            pushed_result = self.run_cmd(["git", "push", "origin", f"HEAD:refs/heads/{branch}"], cwd=worktree, timeout=120)
            if pushed_result.rc != 0:
                return finish({"status": "REJECT", "reason": "unique draft branch push failed"})
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
                self._remove_remote_branch(worktree, branch)
                pushed = False
                return finish({"status": "REJECT", "reason": "GitHub did not create the draft PR"})
            draft = self.run_cmd(["gh", "pr", "view", pr_url, "--json", "isDraft", "--jq", ".isDraft"], cwd=worktree, timeout=30)
            if draft.rc != 0 or draft.stdout.strip().lower() != "true":
                self.run_cmd(["gh", "pr", "close", pr_url], cwd=worktree, timeout=60)
                self._remove_remote_branch(worktree, branch)
                pushed = False
                return finish({"status": "REJECT", "reason": "GitHub did not preserve draft status", "pr_url": pr_url})
            self._record_publication(fingerprint, repo_name, pr_url, branch)
            return finish({
                "status": "DRAFT_PR_OPENED",
                "fingerprint": fingerprint,
                "pr_url": pr_url,
                "branch": branch,
                "source_ref": source_ref,
                "files": list(validated.paths),
                "verification": " ".join(verification_argv),
                "proof": str(result_path),
            })
        finally:
            removed = self._cleanup(repo, worktree)
            if result_path.exists():
                saved = json.loads(result_path.read_text(encoding="utf-8"))
                saved["worktree_removed"] = removed
                saved["remote_branch_created"] = pushed
                result_path.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n", encoding="utf-8")
