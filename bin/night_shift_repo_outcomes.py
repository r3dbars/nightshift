"""Bounded repository-yield memory for portfolio prioritization."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile


def load_repo_outcomes(path: Path, limit: int = 500) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    rows: list[dict] = []
    for line in lines[-limit:]:
        try:
            row = json.loads(line)
        except (TypeError, ValueError):
            continue
        if isinstance(row, dict) and row.get("repo"):
            rows.append(row)
    return rows


def outcome_ledger_summary(rows: list[dict]) -> dict[str, int | float]:
    """Aggregate durable run and review signals without treating candidates as wins."""
    run_rows = [row for row in rows if row.get("kind") not in {"feedback", "feedback-compatibility"}]
    verified = sum(int(row.get("verified_drafts") or 0) for row in run_rows)
    verified_tokens = sum(int(row.get("verified_outcome_tokens") or 0) for row in run_rows)
    return {
        "runs": len(run_rows),
        "verified_drafts": verified,
        "candidate_only_candidates": sum(int(row.get("candidate_only_candidates") or 0) for row in run_rows),
        "estimated_tokens": sum(int(row.get("estimated_tokens") or 0) for row in run_rows),
        "tokens_per_verified_draft": round(verified_tokens / verified, 4) if verified else 0,
        "useful_feedback": sum(int(row.get("feedback_useful") or 0) for row in rows),
        "useful_verified_feedback": sum(int(row.get("useful_verified_feedback") or 0) for row in rows),
        "useful_candidate_feedback": sum(int(row.get("useful_candidate_feedback") or 0) for row in rows),
        "accepted_verified_outcomes": sum(int(row.get("human_outcome_accepted") or 0) for row in rows if row.get("feedback_verified")),
        "revised_verified_outcomes": sum(int(row.get("human_outcome_revised") or 0) for row in rows if row.get("feedback_verified")),
        "rejected_verified_outcomes": sum(int(row.get("human_outcome_rejected") or 0) for row in rows if row.get("feedback_verified")),
        "hosted_draft_prs": sum(int(row.get("draft_pr_opened") or 0) for row in run_rows),
        "hosted_green_draft_prs": sum(int(row.get("hosted_checks_state") in {"pass", "passed"}) for row in run_rows),
    }


def repo_outcome_adjustment(rows: list[dict], repo: str, limit: int = 8) -> tuple[int, dict]:
    recent = [row for row in rows if row.get("repo") == repo][-limit:]
    points = 0
    productive = 0
    candidate_only_runs = 0
    candidate_only_candidates = 0
    wasted = 0
    useful_feedback = 0
    not_useful_feedback = 0
    useful_verified_feedback = 0
    useful_candidate_feedback = 0
    accepted_verified_outcomes = 0
    revised_verified_outcomes = 0
    rejected_verified_outcomes = 0
    hosted_prs = 0
    hosted_green = 0
    hosted_failed = 0
    for row in recent:
        verified = int(row.get("verified_drafts") or 0)
        candidates = int(row.get("accepted_candidates") or 0)
        tokens = int(row.get("estimated_tokens") or 0)
        useful_feedback += int(row.get("feedback_useful") or 0)
        not_useful_feedback += int(row.get("feedback_not_useful") or 0)
        if row.get("feedback_useful"):
            if row.get("feedback_verified") or row.get("feedback_outcome_status") in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}:
                useful_verified_feedback += 1
            else:
                useful_candidate_feedback += 1
        if row.get("feedback_verified"):
            accepted_verified_outcomes += int(row.get("human_outcome_accepted") or 0)
            revised_verified_outcomes += int(row.get("human_outcome_revised") or 0)
            rejected_verified_outcomes += int(row.get("human_outcome_rejected") or 0)
        if int(row.get("draft_pr_opened") or 0):
            hosted_prs += 1
            if str(row.get("hosted_checks_state") or "") in {"pass", "passed"}:
                hosted_green += 1
            elif str(row.get("hosted_checks_state") or "") in {"failed", "unknown"}:
                hosted_failed += 1
        if verified:
            points += 25
            productive += 1
        elif candidates:
            candidate_only_runs += 1
            candidate_only_candidates += int(row.get("candidate_only_candidates") or candidates)
        elif tokens >= 1000:
            points -= 10
            wasted += 1
    points += min(useful_feedback * 25, 50)
    points -= min(not_useful_feedback * 25, 50)
    points += min(accepted_verified_outcomes * 35, 50)
    points += min(revised_verified_outcomes * 10, 20)
    points -= min(rejected_verified_outcomes * 30, 50)
    return max(-40, min(50, points)), {
        "recent_runs": len(recent),
        "productive_runs": productive,
        "verified_runs": productive,
        "candidate_only_runs": candidate_only_runs,
        "candidate_only_candidates": candidate_only_candidates,
        "wasted_token_runs": wasted,
        "useful_feedback": useful_feedback,
        "not_useful_feedback": not_useful_feedback,
        "useful_verified_feedback": useful_verified_feedback,
        "useful_candidate_feedback": useful_candidate_feedback,
        "accepted_verified_outcomes": accepted_verified_outcomes,
        "revised_verified_outcomes": revised_verified_outcomes,
        "rejected_verified_outcomes": rejected_verified_outcomes,
        "hosted_draft_prs": hosted_prs,
        "hosted_green_draft_prs": hosted_green,
        "hosted_failed_or_unknown_draft_prs": hosted_failed,
    }


def append_repo_outcome(path: Path, row: dict, limit: int = 500) -> None:
    existing = load_repo_outcomes(path, limit=limit)
    rows = [*existing[-max(0, limit - 1):], row]
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(json.dumps(item, sort_keys=True) for item in rows) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
