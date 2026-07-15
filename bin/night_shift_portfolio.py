from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable


def parse_json_text(text: str, default):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return default


def iso_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        return None


def status_check_failed(check: dict) -> bool:
    """Treat GitHub check runs and status contexts consistently."""
    state = str(check.get("conclusion") or check.get("state") or "").upper()
    return state in {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"}


class PortfolioEngine:
    GITHUB_SLUG_RE = re.compile(
        r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)/"
        r"(?P<repo>[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?)"
    )

    def __init__(
        self,
        run_cmd: Callable,
        repo_cache_root: Path,
        task_history_path: Path,
        now_stamp: Callable[[], str],
        outcome_adjustment: Callable[[str], tuple[int, dict]] | None = None,
    ) -> None:
        self.run_cmd = run_cmd
        self.repo_cache_root = repo_cache_root
        self.task_history_path = task_history_path
        self.now_stamp = now_stamp
        self.outcome_adjustment = outcome_adjustment or (lambda _slug: (0, {}))

    def repo_slug(self, repo: Path | None) -> str:
        if not repo:
            return ""
        remote = self.run_cmd(["git", "remote", "get-url", "origin"], cwd=repo, timeout=20)
        value = remote.stdout.strip()
        if remote.rc != 0 or not value:
            return ""
        match = re.fullmatch(
            r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
            r"([^/]+/[^/]+?)(?:\.git)?/?",
            value,
        )
        return match.group(1) if match else ""

    def authenticated_owner(self) -> str:
        if not shutil.which("gh"):
            return ""
        user = self.run_cmd(["gh", "api", "user", "--jq", ".login"], timeout=30)
        return user.stdout.strip() if user.rc == 0 else ""

    def owned_slug(self, slug: str, owner: str) -> tuple[str, str] | None:
        match = self.GITHUB_SLUG_RE.fullmatch(slug or "")
        if not match or not owner or match.group("owner").casefold() != owner.casefold():
            return None
        return match.group("owner"), match.group("repo")

    @classmethod
    def normalize_priority_repos(cls, value) -> list[str]:
        values = [value] if isinstance(value, str) else (value or [])
        normalized: list[str] = []
        seen: set[str] = set()
        for item in values:
            slug = str(item).strip().removesuffix(".git")
            key = slug.casefold()
            if cls.GITHUB_SLUG_RE.fullmatch(slug) and key not in seen:
                normalized.append(slug)
                seen.add(key)
        return normalized

    @staticmethod
    def candidates_for_signal_scan(
        candidates: list[dict], max_repos: int, required_slugs: set[str]
    ) -> list[dict]:
        """Scan the ranked window plus any explicit repos outside it."""
        limit = max(10, max_repos * 4)
        selected = list(candidates[:limit])
        selected_keys = {str(row.get("slug") or "").casefold() for row in selected}
        required_keys = {str(slug).casefold() for slug in required_slugs if slug}
        for candidate in candidates[limit:]:
            key = str(candidate.get("slug") or "").casefold()
            if key in required_keys and key not in selected_keys:
                selected.append(candidate)
                selected_keys.add(key)
        return selected

    @staticmethod
    def select_ranked_rows(rows: list[dict], max_repos: int) -> list[dict]:
        limit = max(1, max_repos)
        ranked = sorted(rows, key=lambda row: (-int(row.get("score", 0)), row.get("slug", "")))
        selected = ranked[:limit]
        primary = next((row for row in ranked if row.get("primary")), None)
        required = ([primary] if primary else []) + [
            row for row in ranked if row.get("priority") and row is not primary
        ]
        for required_row in required:
            if any(row is required_row for row in selected):
                continue
            if required_row is primary:
                replacement_index = len(selected) - 1
            else:
                replacement_index = next(
                    (
                        index
                        for index in range(len(selected) - 1, -1, -1)
                        if not selected[index].get("primary") and not selected[index].get("priority")
                    ),
                    None,
                )
            if replacement_index is not None:
                selected[replacement_index] = required_row
        selected.sort(key=lambda row: (-int(row.get("score", 0)), row.get("slug", "")))
        return selected

    @staticmethod
    def pull_request_counts(prs: list[dict]) -> tuple[int, int, int]:
        actionable = 0
        ready = 0
        drafts = 0
        for pr in prs:
            checks = pr.get("statusCheckRollup") or []
            failed = any(status_check_failed(check) for check in checks)
            if failed or pr.get("reviewDecision") == "CHANGES_REQUESTED":
                actionable += 1
            elif pr.get("isDraft"):
                drafts += 1
            else:
                ready += 1
        return actionable, ready, drafts

    @classmethod
    def selection_reason(cls, item: dict) -> str:
        """Explain the strongest reason this repository received a slot."""
        outcome = item.get("outcome_summary") or {}
        outcome_reason = ""
        if int(outcome.get("useful_feedback") or 0) > 0:
            outcome_reason = "you marked recent work here useful"
        elif int(outcome.get("not_useful_feedback") or 0) > 0:
            outcome_reason = "cooling down after recent low-value work"
        if item.get("primary"):
            return "; ".join(filter(None, ("your current project", outcome_reason)))
        if item.get("priority"):
            return "; ".join(filter(None, ("saved priority", outcome_reason)))
        if outcome_reason:
            return outcome_reason
        signals = item.get("signals") or {}
        if signals.get("failed_runs"):
            return "recent failing checks"
        actionable_prs = int(signals.get("actionable_prs") or 0)
        ready_prs = int(signals.get("ready_prs") or 0)
        draft_prs = int(signals.get("draft_prs") or 0)
        if not actionable_prs and not ready_prs and not draft_prs:
            actionable_prs, ready_prs, draft_prs = cls.pull_request_counts(signals.get("prs") or [])
        if actionable_prs:
            return "pull requests need review or fixes"
        if ready_prs:
            return "ready-to-merge pull requests"
        if draft_prs:
            return "open draft pull requests"
        if signals.get("issues"):
            return "open GitHub issues"
        return "recent activity"

    def github_repo_signals(self, slug: str, default_branch: str = "") -> dict:
        empty = {"prs": [], "issues": [], "failed_runs": [], "score": 0}
        if not slug or not shutil.which("gh"):
            return empty
        prs_result = self.run_cmd(
            [
                "gh",
                "pr",
                "list",
                "-R",
                slug,
                "--limit",
                "30",
                "--json",
                "number,title,isDraft,reviewDecision,statusCheckRollup,updatedAt,url,headRefOid,headRefName",
            ],
            timeout=60,
        )
        issues_result = self.run_cmd(
            ["gh", "issue", "list", "-R", slug, "--limit", "30", "--json", "number,title,labels,updatedAt,url"],
            timeout=60,
        )
        runs_result = self.run_cmd(
            [
                "gh",
                "run",
                "list",
                "-R",
                slug,
                "--limit",
                "30",
                "--json",
                "databaseId,name,workflowName,headBranch,headSha,updatedAt,status,conclusion,url",
            ],
            timeout=60,
        )
        prs = parse_json_text(prs_result.stdout, []) if prs_result.rc == 0 else []
        issues = parse_json_text(issues_result.stdout, []) if issues_result.rc == 0 else []
        all_runs = parse_json_text(runs_result.stdout, []) if runs_result.rc == 0 else []
        latest_runs: dict[str, dict] = {}
        for run in all_runs:
            key = f"{run.get('workflowName') or run.get('name')}:{run.get('headBranch')}"
            current_time = iso_datetime(run.get("updatedAt", "")) or datetime.min.replace(tzinfo=timezone.utc)
            previous_time = iso_datetime((latest_runs.get(key) or {}).get("updatedAt", "")) or datetime.min.replace(tzinfo=timezone.utc)
            if key not in latest_runs or current_time > previous_time:
                latest_runs[key] = run
        failed_runs = [
            run for run in latest_runs.values()
            if run.get("status") == "completed" and run.get("conclusion") == "failure"
        ]
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        failed_runs = [
            row for row in failed_runs
            if not iso_datetime(row.get("updatedAt", "")) or iso_datetime(row.get("updatedAt", "")) >= recent_cutoff
        ]
        active_branches = {str(pr.get("headRefName") or "") for pr in prs}
        if default_branch:
            active_branches.add(default_branch)
        active_branches.discard("")
        if active_branches:
            failed_runs = [row for row in failed_runs if row.get("headBranch") in active_branches]
        score = min(len(failed_runs), 3) * 140
        actionable_prs, ready_prs, draft_prs = self.pull_request_counts(prs)
        score += min(actionable_prs, 3) * 120
        score += min(ready_prs, 3) * 50
        score += min(draft_prs, 3) * 15
        score += min(len(issues), 5) * 10
        return {
            "prs": prs,
            "issues": issues,
            "failed_runs": failed_runs,
            "actionable_prs": actionable_prs,
            "ready_prs": ready_prs,
            "draft_prs": draft_prs,
            "score": score,
        }

    def discover(
        self,
        primary_repo: Path | None,
        active_days: int = 14,
        max_repos: int = 3,
        priority_repos: list[str] | None = None,
    ) -> list[dict]:
        primary_slug = self.repo_slug(primary_repo)
        primary_key = primary_slug.casefold()
        priority_keys = {slug.casefold() for slug in self.normalize_priority_repos(priority_repos)}
        rows: list[dict] = []
        if shutil.which("gh"):
            owner = self.authenticated_owner()
            if owner:
                listed = self.run_cmd(
                    [
                        "gh",
                        "repo",
                        "list",
                        owner,
                        "--limit",
                        "100",
                        "--json",
                        "nameWithOwner,pushedAt,isPrivate,isArchived,isFork,defaultBranchRef,url",
                    ],
                    timeout=90,
                )
                if listed.rc == 0:
                    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, active_days))
                    candidates: list[dict] = []
                    for item in parse_json_text(listed.stdout, []):
                        pushed = iso_datetime(item.get("pushedAt", ""))
                        if item.get("isArchived") or item.get("isFork") or not pushed or pushed < cutoff:
                            continue
                        slug = item.get("nameWithOwner", "")
                        if not self.owned_slug(slug, owner):
                            continue
                        branch = (item.get("defaultBranchRef") or {}).get("name") or "main"
                        age_hours = max(0, (datetime.now(timezone.utc) - pushed).total_seconds() / 3600)
                        candidates.append(
                            {
                                "slug": slug,
                                "pushed_at": item.get("pushedAt", ""),
                                "private": bool(item.get("isPrivate")),
                                "default_branch": branch,
                                "url": item.get("url", ""),
                                "primary": slug.casefold() == primary_key,
                                "priority": slug.casefold() in priority_keys,
                                "activity_score": max(0, 80 - int(age_hours / 6)),
                            }
                        )
                    candidates.sort(
                        key=lambda row: (
                            not row.get("primary", False),
                            -int(row.get("activity_score", 0)),
                            row.get("slug", ""),
                        )
                    )
                    required_slugs = priority_keys | (
                        {primary_key} if primary_key else set()
                    )
                    for candidate in self.candidates_for_signal_scan(
                        candidates, max_repos, required_slugs
                    ):
                        signals = self.github_repo_signals(candidate["slug"], candidate["default_branch"])
                        outcome_adjustment, outcome_summary = self.outcome_adjustment(candidate["slug"])
                        candidate["signals"] = signals
                        candidate["outcome_adjustment"] = outcome_adjustment
                        candidate["outcome_summary"] = outcome_summary
                        candidate["score"] = (
                            signals["score"]
                            + candidate.pop("activity_score")
                            + (40 if candidate.get("primary") else 0)
                            + (300 if candidate.get("priority") else 0)
                            + outcome_adjustment
                        )
                        rows.append(candidate)
        if primary_repo and not any(row.get("primary") for row in rows):
            current_branch = self.run_cmd(["git", "branch", "--show-current"], cwd=primary_repo, timeout=20)
            fallback_branch = current_branch.stdout.strip() if current_branch.rc == 0 else "main"
            rows.append(
                {
                    "slug": primary_slug or primary_repo.name,
                    "pushed_at": "",
                    "private": True,
                    "default_branch": fallback_branch or "main",
                    "url": "",
                    "primary": True,
                    "priority": primary_key in priority_keys,
                    "signals": self.github_repo_signals(primary_slug, fallback_branch or "main"),
                    "score": 1000,
                    "path": str(primary_repo),
                }
            )
        return self.select_ranked_rows(rows, max_repos)

    def ensure_checkout(self, item: dict, primary_repo: Path | None) -> tuple[Path | None, str]:
        if item.get("primary") and primary_repo:
            return primary_repo, "primary checkout (read only)"
        slug = item.get("slug", "")
        owner = self.authenticated_owner()
        parts = self.owned_slug(slug, owner)
        if not parts:
            return None, "GitHub checkout rejected: repo is not strictly owned by the authenticated user"
        self.repo_cache_root.mkdir(parents=True, exist_ok=True)
        cache_root = self.repo_cache_root.resolve()
        cache_name = f"{parts[0]}--{parts[1]}-{hashlib.sha256(slug.encode()).hexdigest()[:12]}"
        target = self.repo_cache_root / cache_name
        if target.is_symlink():
            return None, "GitHub checkout rejected: cache target is a symlink"
        if target.resolve(strict=False).parent != cache_root:
            return None, "GitHub checkout rejected: cache path escapes its root"
        if not target.exists():
            cloned = self.run_cmd(["gh", "repo", "clone", slug, target, "--", "--filter=blob:none"], timeout=600)
            if cloned.rc != 0:
                return None, (cloned.stderr or cloned.stdout or "clone failed")[:240]
        if target.is_symlink() or not target.is_dir():
            return None, "GitHub checkout rejected: cache target is not a real directory"
        cached_slug = self.repo_slug(target)
        if not self.owned_slug(cached_slug, owner) or cached_slug.casefold() != slug.casefold():
            return None, "GitHub checkout rejected: cached origin does not match the expected repo"
        dirty = self.run_cmd(["git", "status", "--porcelain"], cwd=target, timeout=30)
        if dirty.rc != 0 or dirty.stdout.strip():
            quarantine = target.with_name(f"{target.name}-quarantine-{self.now_stamp()}")
            try:
                target.rename(quarantine)
            except OSError as exc:
                return None, f"Night Shift cache needs repair and could not be quarantined: {exc}"
            cloned = self.run_cmd(["gh", "repo", "clone", slug, target, "--", "--filter=blob:none"], timeout=600)
            if cloned.rc != 0:
                return None, (cloned.stderr or cloned.stdout or "clean re-clone failed")[:240]
            if target.is_symlink() or not target.is_dir():
                return None, "GitHub checkout rejected: cache target is not a real directory"
            cached_slug = self.repo_slug(target)
            if not self.owned_slug(cached_slug, owner) or cached_slug.casefold() != slug.casefold():
                return None, "GitHub checkout rejected: re-cloned origin does not match the expected repo"
        fetched = self.run_cmd(["git", "fetch", "--prune", "origin"], cwd=target, timeout=180)
        if fetched.rc != 0:
            return None, (fetched.stderr or fetched.stdout or "fetch failed")[:240]
        branch = item.get("default_branch") or "main"
        switched = self.run_cmd(["git", "switch", branch], cwd=target, timeout=60)
        if switched.rc != 0:
            switched = self.run_cmd(["git", "switch", "-c", branch, f"origin/{branch}"], cwd=target, timeout=60)
        if switched.rc != 0:
            return None, (switched.stderr or switched.stdout or "branch switch failed")[:240]
        updated = self.run_cmd(["git", "merge", "--ff-only", f"origin/{branch}"], cwd=target, timeout=120)
        if updated.rc != 0:
            return None, (updated.stderr or updated.stdout or "fast-forward failed")[:240]
        return target, "cached GitHub checkout"

    def load_history(self) -> dict[str, dict]:
        history: dict[str, dict] = {}
        try:
            lines = self.task_history_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return history
        for line in lines:
            row = parse_json_text(line, {})
            fingerprint = row.get("fingerprint")
            if fingerprint:
                history[fingerprint] = row
        return history

    @staticmethod
    def task_fingerprint(repo_name: str, head: str, task: dict) -> str:
        recurrence = str(task.get("recurrence") or "")
        recurrence_bucket = ""
        if recurrence == "daily":
            recurrence_bucket = datetime.now(timezone.utc).date().isoformat()
        elif recurrence == "weekly":
            recurrence_bucket = datetime.now(timezone.utc).strftime("%G-W%V")
        payload = {
            "repo": repo_name,
            "head": head,
            "slug": task.get("slug", ""),
            "kind": task.get("kind", ""),
            "files": sorted(task.get("files") or []),
            "signal": task.get("signal", ""),
            "source_ref": task.get("source_ref", ""),
            "recurrence": recurrence,
            "recurrence_bucket": recurrence_bucket,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def append_history(self, rows: list[dict]) -> None:
        if not rows:
            return
        self.task_history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.task_history_path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
