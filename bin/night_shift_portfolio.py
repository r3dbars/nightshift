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


class PortfolioEngine:
    def __init__(
        self,
        run_cmd: Callable,
        repo_cache_root: Path,
        task_history_path: Path,
        now_stamp: Callable[[], str],
    ) -> None:
        self.run_cmd = run_cmd
        self.repo_cache_root = repo_cache_root
        self.task_history_path = task_history_path
        self.now_stamp = now_stamp

    def repo_slug(self, repo: Path | None) -> str:
        if not repo:
            return ""
        remote = self.run_cmd(["git", "remote", "get-url", "origin"], cwd=repo, timeout=20)
        value = remote.stdout.strip()
        if remote.rc != 0 or not value:
            return ""
        match = re.search(r"github\.com[/:]([^/]+/[^/]+?)(?:\.git)?$", value)
        return match.group(1) if match else ""

    def github_repo_signals(self, slug: str) -> dict:
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
                "number,title,isDraft,reviewDecision,statusCheckRollup,updatedAt,url",
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
            if key not in latest_runs:
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
        score = min(len(failed_runs), 3) * 140
        for pr in prs:
            checks = pr.get("statusCheckRollup") or []
            failed = any(check.get("conclusion") in {"FAILURE", "TIMED_OUT", "CANCELLED"} for check in checks)
            if failed or pr.get("reviewDecision") == "CHANGES_REQUESTED":
                score += 120
            elif pr.get("isDraft"):
                score += 30
            else:
                score += 50
        score += min(len(issues), 5) * 15
        return {"prs": prs, "issues": issues, "failed_runs": failed_runs, "score": score}

    def discover(self, primary_repo: Path | None, active_days: int = 14, max_repos: int = 3) -> list[dict]:
        primary_slug = self.repo_slug(primary_repo)
        rows: list[dict] = []
        if shutil.which("gh"):
            user = self.run_cmd(["gh", "api", "user", "--jq", ".login"], timeout=30)
            if user.rc == 0 and user.stdout.strip():
                listed = self.run_cmd(
                    [
                        "gh",
                        "repo",
                        "list",
                        user.stdout.strip(),
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
                        branch = (item.get("defaultBranchRef") or {}).get("name") or "main"
                        age_hours = max(0, (datetime.now(timezone.utc) - pushed).total_seconds() / 3600)
                        candidates.append(
                            {
                                "slug": slug,
                                "pushed_at": item.get("pushedAt", ""),
                                "private": bool(item.get("isPrivate")),
                                "default_branch": branch,
                                "url": item.get("url", ""),
                                "primary": slug == primary_slug,
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
                    for candidate in candidates[: max(10, max_repos * 4)]:
                        signals = self.github_repo_signals(candidate["slug"])
                        candidate["signals"] = signals
                        candidate["score"] = (
                            signals["score"]
                            + candidate.pop("activity_score")
                            + (40 if candidate.get("primary") else 0)
                        )
                        rows.append(candidate)
        if primary_repo and not any(row.get("primary") for row in rows):
            rows.append(
                {
                    "slug": primary_slug or primary_repo.name,
                    "pushed_at": "",
                    "private": True,
                    "default_branch": "main",
                    "url": "",
                    "primary": True,
                    "signals": self.github_repo_signals(primary_slug),
                    "score": 1000,
                    "path": str(primary_repo),
                }
            )
        rows.sort(key=lambda row: (-int(row.get("score", 0)), row.get("slug", "")))
        return rows[: max(1, max_repos)]

    def ensure_checkout(self, item: dict, primary_repo: Path | None) -> tuple[Path | None, str]:
        if item.get("primary") and primary_repo:
            return primary_repo, "primary checkout (read only)"
        slug = item.get("slug", "")
        if not slug or "/" not in slug or not shutil.which("gh"):
            return None, "GitHub checkout unavailable"
        self.repo_cache_root.mkdir(parents=True, exist_ok=True)
        target = self.repo_cache_root / re.sub(r"[^A-Za-z0-9._-]+", "--", slug)
        if not target.exists():
            cloned = self.run_cmd(["gh", "repo", "clone", slug, target, "--", "--filter=blob:none"], timeout=600)
            if cloned.rc != 0:
                return None, (cloned.stderr or cloned.stdout or "clone failed")[:240]
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
        payload = {
            "repo": repo_name,
            "head": head,
            "slug": task.get("slug", ""),
            "kind": task.get("kind", ""),
            "files": sorted(task.get("files") or []),
            "signal": task.get("signal", ""),
            "source_ref": task.get("source_ref", ""),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def append_history(self, rows: list[dict]) -> None:
        if not rows:
            return
        self.task_history_path.parent.mkdir(parents=True, exist_ok=True)
        with self.task_history_path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
