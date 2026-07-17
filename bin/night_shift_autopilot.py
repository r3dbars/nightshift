from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

MAX_DRAFT_ATTEMPTS_PER_REPO = 4
MAX_VERIFIED_DRAFTS_PER_REPO = 2
MAX_DRAFT_PRS_PER_REPO = 1
MAX_DRAFT_PRS_PER_SHIFT = 3


@dataclass
class AutopilotCycleState:
    ledger: Path
    rows: list[dict] = field(default_factory=list)
    attempted_counts: dict[str, int] = field(default_factory=dict)
    verified_counts: dict[str, int] = field(default_factory=dict)
    published_counts: dict[str, int] = field(default_factory=dict)
    published_total: int = 0
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
            and self.verified_counts.get(str(repo or ""), 0) < MAX_VERIFIED_DRAFTS_PER_REPO
            and self.attempted_counts.get(str(repo or ""), 0) < MAX_DRAFT_ATTEMPTS_PER_REPO
        )

    def finish_draft_attempt(self, row: dict, draft: dict | None) -> None:
        repo = str(row.get("repo") or "")
        self.attempted_counts[repo] = self.attempted_counts.get(repo, 0) + 1
        if draft is not None:
            row["draft"] = draft
            if str(draft.get("status") or "") in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}:
                self.verified_counts[repo] = self.verified_counts.get(repo, 0) + 1

    def should_skip_attempted_repo(self, repo: str) -> bool:
        """Stop after a small bounded budget, or after a verified draft."""
        name = str(repo or "")
        return (
            self.verified_counts.get(name, 0) >= MAX_VERIFIED_DRAFTS_PER_REPO
            or self.attempted_counts.get(name, 0) >= MAX_DRAFT_ATTEMPTS_PER_REPO
        )

    def record_attempted_skip(self, *, repo: str, checkout: Path) -> dict:
        name = str(repo or "")
        if self.verified_counts.get(name, 0) >= MAX_VERIFIED_DRAFTS_PER_REPO:
            reason = "verified draft limit reached for this repo during this shift"
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

    @staticmethod
    def may_publish(permission: str, allow_draft_prs: bool, draft_status: str) -> bool:
        return (
            permission == "draft-prs"
            and allow_draft_prs
            and draft_status in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}
        )

    def may_publish_now(
        self,
        repo: str,
        permission: str,
        allow_draft_prs: bool,
        draft_status: str,
    ) -> bool:
        name = str(repo or "")
        return (
            self.may_publish(permission, allow_draft_prs, draft_status)
            and self.published_counts.get(name, 0) < MAX_DRAFT_PRS_PER_REPO
            and self.published_total < MAX_DRAFT_PRS_PER_SHIFT
        )

    def attach_publish(self, row: dict, publish: dict) -> None:
        row["publish"] = publish
        publication_consumed = bool(publish.get("pr_url")) or publish.get("status") == "REMOTE_CLEANUP_REQUIRED"
        if publication_consumed:
            repo = str(row.get("repo") or "")
            self.published_counts[repo] = self.published_counts.get(repo, 0) + 1
            self.published_total += 1
        hosted_state = str((publish.get("hosted_checks") or {}).get("state") or "")
        if publish.get("status") == "REMOTE_CLEANUP_REQUIRED" or hosted_state in {
            "failed",
            "pending",
            "unknown",
        }:
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
            or str(((row.get("publish") or {}).get("hosted_checks") or {}).get("state") or "")
            in {"failed", "pending", "unknown"}
            for row in self.rows
        )
