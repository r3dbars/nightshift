from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

MAX_DRAFT_ATTEMPTS_PER_REPO = 3


@dataclass
class AutopilotCycleState:
    ledger: Path
    rows: list[dict] = field(default_factory=list)
    drafted_repos: set[str] = field(default_factory=set)
    attempted_repos: set[str] = field(default_factory=set)
    attempted_counts: dict[str, int] = field(default_factory=dict)
    verified_repos: set[str] = field(default_factory=set)
    cycle: int = 0
    status: str = "GREEN"
    cycle_had_work: bool = False

    def start_cycle(self) -> int:
        self.cycle += 1
        self.cycle_had_work = False
        return self.cycle

    def no_prepared_repositories(self) -> None:
        self.status = "YELLOW"

    def record_child(
        self,
        *,
        repo: str,
        checkout: Path,
        child_ledger: Path,
        return_code: int,
        child_is_green: bool,
        planned_count: int,
    ) -> dict:
        if return_code != 0 or not child_is_green:
            self.status = "YELLOW"
        self.cycle_had_work = self.cycle_had_work or planned_count > 0
        return {
            "cycle": self.cycle,
            "repo": repo,
            "checkout": str(checkout.expanduser().resolve()),
            "ledger": str(child_ledger),
            "rc": return_code,
            "new_tasks": planned_count,
        }

    def may_draft(self, repo: str, execute_drafts: bool, permission: str) -> bool:
        return (
            execute_drafts
            and permission in {"draft-local", "draft-prs"}
            and repo not in self.verified_repos
            and self.attempted_counts.get(str(repo or ""), 0) < MAX_DRAFT_ATTEMPTS_PER_REPO
        )

    def finish_draft_attempt(self, row: dict, draft: dict | None) -> None:
        repo = str(row.get("repo") or "")
        self.attempted_repos.add(repo)
        self.attempted_counts[repo] = self.attempted_counts.get(repo, 0) + 1
        if draft is not None:
            row["draft"] = draft
            if str(draft.get("status") or "") in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}:
                self.verified_repos.add(repo)
        self.drafted_repos.add(str(row.get("repo") or ""))

    def should_skip_attempted_repo(self, repo: str) -> bool:
        """Stop after a small bounded budget, or after a verified draft."""
        name = str(repo or "")
        return (
            name in self.verified_repos
            or self.attempted_counts.get(name, 0) >= MAX_DRAFT_ATTEMPTS_PER_REPO
        )

    def should_skip_verified_repo(self, repo: str) -> bool:
        """Avoid more model calls after this repo already produced a verified draft."""
        return str(repo or "") in self.verified_repos

    def record_attempted_skip(self, *, repo: str, checkout: Path) -> dict:
        name = str(repo or "")
        if name in self.verified_repos:
            reason = "verified draft already produced for this repo during this shift"
        else:
            reason = "bounded draft-attempt budget reached for this repo during this shift; retry next shift"
        return {
            "cycle": self.cycle,
            "repo": repo,
            "checkout": str(checkout.expanduser().resolve()),
            "ledger": "",
            "rc": 0,
            "new_tasks": 0,
            "skip_reason": reason,
        }

    def record_verified_skip(self, *, repo: str, checkout: Path) -> dict:
        return self.record_attempted_skip(repo=repo, checkout=checkout)

    @staticmethod
    def may_publish(permission: str, allow_draft_prs: bool, draft_status: str) -> bool:
        return (
            permission == "draft-prs"
            and allow_draft_prs
            and draft_status in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}
        )

    def attach_publish(self, row: dict, publish: dict) -> None:
        row["publish"] = publish
        hosted_state = str((publish.get("hosted_checks") or {}).get("state") or "")
        if publish.get("status") == "REMOTE_CLEANUP_REQUIRED" or hosted_state in {"failed", "unknown"}:
            self.status = "YELLOW"

    def append(self, row: dict) -> None:
        self.rows.append(row)
        (self.ledger / "cycles.json").write_text(
            json.dumps(self.rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def action_required(self) -> bool:
        return not self.rows or any(
            row.get("rc") != 0
            or (row.get("publish") or {}).get("status") == "REMOTE_CLEANUP_REQUIRED"
            for row in self.rows
        )
