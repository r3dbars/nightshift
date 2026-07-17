from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Callable

from night_shift_reporting import friendly_summary


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

    def morning_items(self, rows_by_repo: dict[str, dict] | list[dict]) -> list[dict]:
        """Materialize exact queued tasks without attaching proof to a different task."""
        items: list[dict] = []
        if isinstance(rows_by_repo, dict):
            rows = [
                {**row, "repo": row.get("repo") or repo_name}
                for repo_name, row in rows_by_repo.items()
            ]
        else:
            rows = [row for row in rows_by_repo if isinstance(row, dict)]
        ordered = sorted(
            rows,
            key=lambda row: (
                0
                if (row.get("draft") or {}).get("status") in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}
                else 1,
                int(row.get("portfolio_rank") or 999999),
                -int(row.get("portfolio_score") or 0),
                str(row.get("repo") or "unknown"),
                int(row.get("cycle") or 0),
            ),
        )
        seen: set[tuple[str, str, str, str]] = set()
        for row in ordered:
            repo_name = str(row.get("repo") or "unknown")
            child_path = str(row.get("ledger") or "")
            if not child_path:
                continue
            child = Path(child_path)
            try:
                child_items = json.loads((child / "work-queue.json").read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                child_items = []
            child_items = [item for item in child_items if isinstance(item, dict)]
            if not child_items:
                continue
            draft = row.get("draft") or {}
            candidate_key = str(draft.get("candidate_key") or "")
            fingerprint = str(draft.get("fingerprint") or "")
            if draft and candidate_key:
                matches = [item for item in child_items if str(item.get("key") or "") == candidate_key]
            elif draft and fingerprint:
                matches = [
                    item for item in child_items
                    if str(item.get("fingerprint") or item.get("key") or "") == fingerprint
                ]
            elif draft:
                matches = child_items if len(child_items) == 1 else []
            else:
                matches = child_items[:1]
            if len(matches) != 1:
                continue
            item = matches[0]
            publish = row.get("publish") or {}
            identity = (
                repo_name,
                str(item.get("key") or ""),
                str(draft.get("proof") or draft.get("patch") or ""),
                str(publish.get("pr_url") or ""),
            )
            if identity in seen:
                continue
            seen.add(identity)
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
                "files": draft.get("files") or item.get("files") or [],
                "verification": draft.get("verification") or item.get("tests") or item.get("verification_commands") or "",
                "proof": draft.get("proof") or item.get("proof") or item.get("primary_artifact", ""),
                "patch": draft.get("patch") or "",
                "outcome_status": str(draft.get("status") or ""),
                "pr_url": publish.get("pr_url") or "",
                "publish_status": publish.get("status") or "",
                "hosted_checks_state": str((publish.get("hosted_checks") or {}).get("state") or ""),
                "selection_reason": row.get("portfolio_reason") or "recent activity",
            })
        return items

    @staticmethod
    def signal_summary(row: dict) -> str:
        """Describe the bounded GitHub signals checked for a portfolio row."""
        signals = row.get("portfolio_signals") or {}
        parts = []
        try:
            failed = int(signals.get("failed_runs") or 0)
        except (TypeError, ValueError):
            failed = 0
        if failed:
            parts.append(f"{failed} failed check{'s' if failed != 1 else ''}")
        try:
            prs = int(signals.get("prs") or 0)
        except (TypeError, ValueError):
            prs = 0
        if prs:
            details = []
            for key, label in (
                ("actionable_prs", "needing review or fixes"),
                ("ready_prs", "ready to merge"),
                ("draft_prs", "draft"),
            ):
                try:
                    count = int(signals.get(key) or 0)
                except (TypeError, ValueError):
                    count = 0
                if count:
                    details.append(f"{count} {label}")
            suffix = f" ({', '.join(details)})" if details else ""
            parts.append(f"{prs} pull request{'s' if prs != 1 else ''}{suffix}")
        try:
            issues = int(signals.get("issues") or 0)
        except (TypeError, ValueError):
            issues = 0
        if issues:
            parts.append(f"{issues} issue{'s' if issues != 1 else ''}")
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

    @staticmethod
    def unverified_summary(count: int) -> str:
        """Keep candidate-only results singular and clear in the morning brief."""
        if count == 1:
            return "One possible lead; no deterministic outcome yet."
        return f"{count} possible leads; no deterministic outcome yet."

    @staticmethod
    def morning_choice_heading(items: list[dict]) -> str:
        """Use stronger language only when the portfolio item has proof."""
        if not items:
            return "What I checked:"
        verified = {"PROVEN_REPAIR", "VERIFIED_DRAFT"}
        if len(items) == 1:
            return (
                "One verified outcome to review:"
                if items[0].get("outcome_status") in verified
                else "One possible lead:"
            )
        if all(item.get("outcome_status") in verified for item in items):
            return "Verified outcomes to review:"
        return "Possible leads:"

    @staticmethod
    def run_summary(ledger: Path) -> dict:
        try:
            value = json.loads((ledger / "run-summary.json").read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def run_stop_line(summary: dict) -> str:
        reasons = {
            "deadline": "reached the configured stop limit",
            "stop-file": "was stopped by the user or scheduler",
            "once": "completed its one-cycle run",
            "no-prepared-repositories": "stopped because no repository checkout was available",
            "completed": "completed normally",
            "error": "stopped after an internal error",
        }
        reason = reasons.get(
            str(summary.get("stop_reason") or ""),
            "finished without a recorded stop reason",
        )
        try:
            elapsed = float(summary.get("elapsed_seconds") or 0)
        except (TypeError, ValueError):
            elapsed = 0
        duration = f"{elapsed / 3600:.1f} hours" if elapsed else "an unknown duration"
        cycles = int(summary.get("cycles") or 0)
        repositories = int(summary.get("repositories_visited") or 0)
        return f"- Controller {reason} after {duration}; {cycles} cycles across {repositories} repositories."

    def write_brief(self, ledger: Path, cycle_rows: list[dict], status: str) -> None:
        latest_by_repo: dict[str, dict] = {}
        for row in cycle_rows:
            repo_name = row.get("repo", "unknown")
            if (
                repo_name not in latest_by_repo
                or row.get("new_tasks")
                or row.get("draft")
                or row.get("publish")
            ):
                latest_by_repo[repo_name] = row
        proven = any(
            (row.get("draft") or {}).get("status") in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}
            for row in cycle_rows
        )
        new_candidates = any(row.get("new_tasks", 0) for row in cycle_rows)
        display_status = status
        if status == "GREEN":
            display_status = "GREEN" if proven or not new_candidates else "YELLOW"
        publication_needs_attention = any(
            (row.get("publish") or {}).get("status") == "REMOTE_CLEANUP_REQUIRED"
            or str(((row.get("publish") or {}).get("hosted_checks") or {}).get("state") or "")
            in {"failed", "pending", "unknown"}
            for row in cycle_rows
        )
        if publication_needs_attention and display_status == "GREEN":
            display_status = "YELLOW"
        morning_items = self.morning_items(cycle_rows)
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
        ]
        summary = self.run_summary(ledger)
        if summary:
            lines.extend([
                "Run status:",
                self.run_stop_line(summary),
                f"- Exact run proof: {ledger / 'run-summary.json'}",
                "",
            ])
        lines.append("What Night Shift worked on:")
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
                    summary = self.unverified_summary(int(row["new_tasks"]))
            elif row.get("new_tasks"):
                summary = self.unverified_summary(int(row["new_tasks"]))
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
        publication_rows = [row for row in cycle_rows if row.get("publish")]
        if publication_rows:
            lines.extend(["", "Draft PRs and GitHub checks:"])
            seen_publications: set[tuple[str, str, str, str]] = set()
            for row in publication_rows:
                publish = row.get("publish") or {}
                repo_name = str(row.get("repo") or "unknown")
                identity = (
                    repo_name,
                    str(publish.get("pr_url") or ""),
                    str(publish.get("branch") or ""),
                    str(publish.get("status") or ""),
                )
                if identity in seen_publications:
                    continue
                seen_publications.add(identity)
                destination = publish.get("pr_url") or publish.get("reason") or "no URL recorded"
                lines.append(
                    f"- {repo_name}: {destination} [{publish.get('status') or 'unknown'}]"
                )
                hosted = publish.get("hosted_checks") or {}
                hosted_state = str(hosted.get("state") or "")
                if hosted:
                    lines.append(
                        f"  GitHub checks: {hosted_state or 'unknown'}"
                        f" ({hosted.get('check_count', 0)} reported)"
                    )
                if publish.get("status") == "REMOTE_CLEANUP_REQUIRED":
                    lines.append(
                        "  ACTION REQUIRED: check GitHub and close or delete the reported draft PR or branch."
                    )
                elif hosted_state == "failed":
                    lines.append("  ACTION REQUIRED: review the failing GitHub checks before using this draft.")
                elif hosted_state == "pending":
                    lines.append("  ACTION REQUIRED: wait for GitHub checks to finish before using this draft.")
                elif hosted_state == "unknown":
                    lines.append("  ACTION REQUIRED: GitHub check status could not be confirmed.")
        if morning_items:
            ledger_arg = shlex.quote(str(ledger))
            lines.extend(["", self.morning_choice_heading(morning_items)])
            for item in morning_items[:3]:
                display_summary = friendly_summary(item["summary"])
                lines.append(
                    f"{item['rank']}. {item['repo']}: {display_summary} "
                    f"[{item['score']}] ({item['selection_reason']})"
                )
                if display_summary != item["summary"]:
                    lines.append(f"   Technical detail: {item['summary']}")
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
                "Safe next step: prepare the bounded review pack locally first (nothing is sent):",
                f"- `night-shift handoff --ledger {ledger_arg} --item 1 --agent codex`",
                "- If it says `CLOUD_PREFLIGHT: GREEN` and you want one read-only cloud review, rerun it with `--run --allow-cloud`.",
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
