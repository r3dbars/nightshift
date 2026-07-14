from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Callable


class PortfolioReportEngine:
    def __init__(self, task_history_path: Path, task_family: Callable[[str], str]) -> None:
        self.task_history_path = task_history_path
        self.task_family = task_family

    @staticmethod
    def morning_status(path: Path) -> str:
        if not path.exists():
            return "UNKNOWN"
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^Status: (GREEN|YELLOW|RED)$", text, re.MULTILINE)
        return match.group(1) if match else "UNKNOWN"

    @staticmethod
    def append_bounded_snapshot(path: Path, compact: dict, limit: int = 256) -> None:
        existing = path.read_text(encoding="utf-8", errors="replace").splitlines() if path.exists() else []
        rows = [*existing[-max(0, limit - 1):], json.dumps(compact, sort_keys=True)]
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    @staticmethod
    def write_snapshot(ledger: Path, rows: list[dict], cycle: int | None = None) -> None:
        (ledger / "portfolio.json").write_text(
            json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        lines = ["# GitHub Portfolio", ""]
        for index, row in enumerate(rows, start=1):
            signals = row.get("signals") or {}
            lines.extend([
                f"{index}. {row.get('slug', 'unknown')}",
                f"   Score: {row.get('score', 0)}",
                f"   Recently pushed: {row.get('pushed_at') or 'local checkout'}",
                f"   Signals: PRs={len(signals.get('prs') or [])}, issues={len(signals.get('issues') or [])}, failed runs={len(signals.get('failed_runs') or [])}",
                f"   Checkout: {row.get('checkout_status', 'not prepared')}",
            ])
        if not rows:
            lines.append("No eligible repositories found.")
        (ledger / "portfolio.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if cycle is not None:
            compact = {
                "cycle": cycle,
                "repositories": [
                    {
                        "checkout_ready": bool(row.get("checkout")),
                        "failed_runs": len((row.get("signals") or {}).get("failed_runs") or []),
                        "issues": len((row.get("signals") or {}).get("issues") or []),
                        "outcome_adjustment": int(row.get("outcome_adjustment") or 0),
                        "outcome_summary": row.get("outcome_summary") or {},
                        "primary": bool(row.get("primary")),
                        "prs": len((row.get("signals") or {}).get("prs") or []),
                        "score": int(row.get("score") or 0),
                        "slug": row.get("slug", ""),
                    }
                    for row in rows
                ],
            }
            PortfolioReportEngine.append_bounded_snapshot(
                ledger / "portfolio-snapshots.jsonl", compact
            )

    def morning_items(self, latest_by_repo: dict[str, dict]) -> list[dict]:
        items: list[dict] = []
        ordered = sorted(
            latest_by_repo.items(),
            key=lambda pair: (
                int(pair[1].get("portfolio_rank") or 999999),
                -int(pair[1].get("portfolio_score") or 0),
                pair[0],
            ),
        )
        for repo_name, row in ordered:
            child = Path(row.get("ledger", ""))
            try:
                child_items = json.loads((child / "work-queue.json").read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                child_items = []
            if not child_items or not isinstance(child_items[0], dict):
                continue
            item = child_items[0]
            labels = item.get("labels") or []
            repo_path = row.get("repo_path") or row.get("checkout") or ""
            items.append({
                "rank": len(items) + 1,
                "repo": repo_name,
                "repo_path": str(Path(repo_path).expanduser().resolve()) if repo_path else "",
                "child_ledger": str(child),
                "key": item.get("key", ""),
                "family": self.task_family(
                    labels[0] if labels else str(item.get("key", "")).split(":", 1)[0]
                ),
                "fingerprint": item.get("fingerprint", ""),
                "source_ref": item.get("source_ref", ""),
                "summary": item.get("summary", ""),
                "score": item.get("score", ""),
                "evidence": item.get("evidence", ""),
                "files": item.get("files") or [],
                "verification": item.get("tests") or item.get("verification_commands") or "",
                "proof": item.get("proof") or item.get("primary_artifact", ""),
                "outcome_status": str((row.get("draft") or {}).get("status") or ""),
                "selection_reason": row.get("portfolio_reason") or "recent activity",
            })
        return items

    @staticmethod
    def signal_summary(row: dict) -> str:
        """Describe the bounded GitHub signals checked for a portfolio row."""
        signals = row.get("portfolio_signals") or {}
        parts = []
        for singular, plural, key in (
            ("failed check", "failed checks", "failed_runs"),
            ("pull request", "pull requests", "prs"),
            ("issue", "issues", "issues"),
        ):
            try:
                count = int(signals.get(key) or 0)
            except (TypeError, ValueError):
                count = 0
            if count:
                parts.append(f"{count} {singular if count == 1 else plural}")
        return ", ".join(parts)

    @classmethod
    def no_work_summary(cls, row: dict) -> str:
        """Explain an honest no-work result without turning signals into a claim."""
        signals = row.get("portfolio_signals") or {}
        try:
            failed = int(signals.get("failed_runs") or 0)
        except (TypeError, ValueError):
            failed = 0
        if failed:
            return (
                f"I found {failed} recent failing check(s), but the repo evidence was not "
                "specific enough to make a safe task."
            )
        summary = cls.signal_summary(row)
        if summary:
            return f"I checked {summary}, but none became a safe, specific task tonight."
        return "I checked this repo, but nothing was strong enough to work on safely tonight."

    def write_brief(self, ledger: Path, cycle_rows: list[dict], status: str) -> None:
        latest_by_repo: dict[str, dict] = {}
        for row in cycle_rows:
            repo_name = row.get("repo", "unknown")
            if repo_name not in latest_by_repo or row.get("new_tasks") or row.get("draft"):
                latest_by_repo[repo_name] = row
        proven = any(
            (row.get("draft") or {}).get("status") in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}
            for row in cycle_rows
        )
        new_candidates = any(row.get("new_tasks", 0) for row in cycle_rows)
        display_status = status
        if status == "GREEN":
            display_status = "GREEN" if proven or not new_candidates else "YELLOW"
        morning_items = self.morning_items(latest_by_repo)
        candidate_count = 0
        verified_drafts = 0
        verified_tokens = 0
        for row in cycle_rows:
            outcomes = row.get("outcomes") or {}
            candidates = int(outcomes.get("candidate_count") or 0)
            verified = int(outcomes.get("verified_drafts") or 0)
            if not outcomes and (row.get("draft") or {}).get("status") in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}:
                verified = 1
            candidate_count += candidates
            verified_drafts += verified
            verified_tokens += int(outcomes.get("verified_outcome_tokens") or 0)
        candidate_only = max(0, candidate_count - verified_drafts)
        tokens_per_verified = round(verified_tokens / verified_drafts, 4) if verified_drafts else 0
        (ledger / "morning-items.json").write_text(
            json.dumps(morning_items, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        lines = [
            "# Night Shift Portfolio Brief", "", f"Status: {display_status}", "",
            "Good morning - here is the short version:", "",
            "What Night Shift worked on:",
        ]
        if not latest_by_repo:
            lines.append("- No repository produced a new task this cycle.")
        ordered_rows = sorted(
            latest_by_repo.items(),
            key=lambda pair: (
                int(pair[1].get("portfolio_rank") or 999999),
                -int(pair[1].get("portfolio_score") or 0),
                pair[0],
            ),
        )
        for repo_name, row in ordered_rows:
            child = Path(row.get("ledger", ""))
            summary = self.no_work_summary(row)
            draft = row.get("draft") or {}
            morning = child / "morning.md"
            if draft.get("status") == "PROVEN_REPAIR":
                summary = "1 proven local repair; failing-before and passing-after checks succeeded."
            elif draft.get("status") == "VERIFIED_DRAFT":
                summary = "1 verified local draft; checks passed, your checkout stayed untouched, and the patch is ready for review."
            elif morning.exists():
                text = morning.read_text(encoding="utf-8", errors="replace")
                match = re.search(r"Start here:\n- (.+)", text)
                if match and self.morning_status(morning) == "GREEN":
                    summary = match.group(1).strip()
                elif row.get("new_tasks"):
                    summary = f"{row['new_tasks']} unproven candidate(s); no deterministic outcome."
            reason = row.get("portfolio_reason") or "recent activity"
            lines.extend([f"- {repo_name}: {summary}", f"  Why this repo: {reason}", f"  Proof: {child}"])
            signal_summary = self.signal_summary(row)
            if signal_summary:
                lines.append(f"  GitHub signals checked: {signal_summary}.")
            if draft:
                draft_status = str(draft.get("status") or "unknown")
                draft_reason = str(draft.get("reason") or "")
                guard_reasons = draft.get("guard_reasons") or []
                if not draft_reason and guard_reasons:
                    draft_reason = "; ".join(str(value) for value in guard_reasons)
                if draft_status in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}:
                    draft_detail = draft.get("patch") or draft_reason or "proof recorded"
                else:
                    draft_detail = draft_reason or "not proven"
                lines.append(
                    f"  Draft: {draft_status} | {draft_detail}"
                )
                if draft_status in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}:
                    lines.append("  Next: review the patch above; Night Shift did not change your checkout.")
            publish = row.get("publish") or {}
            if publish:
                lines.append(
                    f"  Draft PR: {publish.get('pr_url') or publish.get('reason', 'not opened')}"
                )
                hosted = publish.get("hosted_checks") or {}
                if hosted:
                    lines.append(
                        f"  GitHub checks: {hosted.get('state', 'unknown')}"
                        f" ({hosted.get('check_count', 0)} reported)"
                    )
                if publish.get("status") == "REMOTE_CLEANUP_REQUIRED":
                    lines.append(
                        "  ACTION REQUIRED: check GitHub and close/delete the reported draft PR or branch."
                    )
        if morning_items:
            ledger_arg = shlex.quote(str(ledger))
            lines.extend(["", "Your morning choices:"])
            for item in morning_items[:3]:
                lines.append(
                    f"{item['rank']}. {item['repo']}: {item['summary']} "
                    f"[{item['score']}] ({item['selection_reason']})"
                )
                if item.get("evidence"):
                    lines.append(f"   Evidence: {item['evidence']}")
                if item.get("files"):
                    lines.append(f"   Files: {', '.join(item['files'])}")
                if item.get("verification"):
                    verification = item["verification"]
                    if isinstance(verification, list):
                        verification = "; ".join(str(command) for command in verification)
                    lines.append(f"   Verify: {verification}")
                if item.get("proof"):
                    lines.append(f"   Proof: {item['proof']}")
            lines.extend([
                "", "Teach the next shift with the exact number shown above:",
                f"- Useful: `night-shift feedback --ledger {ledger_arg} --item 1 --useful`",
                f"- Not useful: `night-shift feedback --ledger {ledger_arg} --item 1 --not-useful --note \"too generic\"`",
                "- Optional result: add `--useful --outcome accepted` if you used it, `--useful --outcome revised` if you changed it, or `--not-useful --outcome rejected` if you discarded it.",
                "- Optional: add `--clarity clear` or `--clarity confusing`, plus `--effort quick`, `--effort some-work`, or `--effort too-much`.",
                "",
                "One-action independent review (read-only; nothing is sent unless you run it):",
                f"- `night-shift handoff --ledger {ledger_arg} --item 1 --agent codex --run --allow-cloud`",
            ])
        else:
            lines.extend([
                "", "What to do next:",
                "- Good news: I checked the repos, but nothing was strong enough to put on your review list this shift.",
                "- Run `night-shift start --yes` tonight. I will rescan fresh repo activity and try again.",
            ])
        lines.extend([
            "", "Run totals:", f"- Repositories visited: {len(latest_by_repo)}",
            f"- Repository batches completed: {len(cycle_rows)}",
            f"- Model candidates: {candidate_count} ({candidate_only} candidate-only)",
            f"- Verified drafts: {verified_drafts}",
            f"- Tokens per verified draft: {tokens_per_verified}",
            f"- Durable task history: {self.task_history_path}", "", "Safety:",
            "- Repository checkouts were read-only unless isolated draft execution was explicitly enabled.",
            "- Tested draft PRs may be opened only when one-time GitHub authorization is saved.",
            "- Nothing was merged, released, deployed, or published.",
        ])
        (ledger / "morning.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
