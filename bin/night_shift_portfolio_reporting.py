from __future__ import annotations

import json
import re
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
        for repo_name, row in sorted(latest_by_repo.items()):
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
            })
        return items

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
        (ledger / "morning-items.json").write_text(
            json.dumps(morning_items, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        lines = [
            "# Night Shift Portfolio Brief", "", f"Status: {display_status}", "",
            "What Night Shift worked on:",
        ]
        if not latest_by_repo:
            lines.append("- No repository produced a new task this cycle.")
        for repo_name, row in sorted(latest_by_repo.items()):
            child = Path(row.get("ledger", ""))
            summary = "I checked this repo, but nothing was strong enough to work on safely tonight."
            draft = row.get("draft") or {}
            morning = child / "morning.md"
            if draft.get("status") == "PROVEN_REPAIR":
                summary = "1 proven local repair; failing-before and passing-after checks succeeded."
            elif draft.get("status") == "VERIFIED_DRAFT":
                summary = "1 verified local draft; full checks passed. Human usefulness review remains."
            elif morning.exists():
                text = morning.read_text(encoding="utf-8", errors="replace")
                match = re.search(r"Start here:\n- (.+)", text)
                if match and self.morning_status(morning) == "GREEN":
                    summary = match.group(1).strip()
                elif row.get("new_tasks"):
                    summary = f"{row['new_tasks']} unproven candidate(s); no deterministic outcome."
            lines.extend([f"- {repo_name}: {summary}", f"  Proof: {child}"])
            if draft:
                lines.append(
                    f"  Draft: {draft.get('status', 'unknown')} | "
                    f"{draft.get('patch') or draft.get('reason', '')}"
                )
            publish = row.get("publish") or {}
            if publish:
                lines.append(
                    f"  Draft PR: {publish.get('pr_url') or publish.get('reason', 'not opened')}"
                )
                if publish.get("status") == "REMOTE_CLEANUP_REQUIRED":
                    lines.append(
                        "  ACTION REQUIRED: check GitHub and close/delete the reported draft PR or branch."
                    )
        if morning_items:
            lines.extend(["", "Your morning choices:"])
            for item in morning_items[:3]:
                lines.append(f"{item['rank']}. {item['repo']}: {item['summary']} [{item['score']}]")
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
                f"- Useful: `night-shift feedback --ledger {ledger} --item 1 --useful`",
                f"- Not useful: `night-shift feedback --ledger {ledger} --item 1 --not-useful`",
            ])
        else:
            lines.extend([
                "", "What to do next:",
                "- Nothing needs your review from this shift.",
                "- Run `night-shift start --yes` tonight. Night Shift will rescan fresh repo activity and try again.",
            ])
        lines.extend([
            "", "Run totals:", f"- Repositories visited: {len(latest_by_repo)}",
            f"- Repository batches completed: {len(cycle_rows)}",
            f"- Durable task history: {self.task_history_path}", "", "Safety:",
            "- Repository checkouts were read-only unless isolated draft execution was explicitly enabled.",
            "- Tested draft PRs may be opened only when one-time GitHub authorization is saved.",
            "- Nothing was merged, released, deployed, or published.",
        ])
        (ledger / "morning.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
