"""Bounded repository-yield memory for portfolio prioritization."""
from __future__ import annotations

import json
from pathlib import Path


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


def repo_outcome_adjustment(rows: list[dict], repo: str, limit: int = 8) -> tuple[int, dict]:
    recent = [row for row in rows if row.get("repo") == repo][-limit:]
    points = 0
    productive = 0
    wasted = 0
    useful_feedback = 0
    not_useful_feedback = 0
    for row in recent:
        verified = int(row.get("verified_drafts") or 0)
        candidates = int(row.get("accepted_candidates") or 0)
        tokens = int(row.get("estimated_tokens") or 0)
        useful_feedback += int(row.get("feedback_useful") or 0)
        not_useful_feedback += int(row.get("feedback_not_useful") or 0)
        if verified:
            points += 25
            productive += 1
        elif candidates:
            points += 10
            productive += 1
        elif tokens >= 1000:
            points -= 10
            wasted += 1
    points += min(useful_feedback * 25, 50)
    points -= min(not_useful_feedback * 25, 50)
    return max(-40, min(50, points)), {
        "recent_runs": len(recent),
        "productive_runs": productive,
        "wasted_token_runs": wasted,
        "useful_feedback": useful_feedback,
        "not_useful_feedback": not_useful_feedback,
    }


def append_repo_outcome(path: Path, row: dict, limit: int = 500) -> None:
    existing = load_repo_outcomes(path, limit=limit)
    rows = [*existing[-max(0, limit - 1):], row]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(item, sort_keys=True) for item in rows) + "\n",
        encoding="utf-8",
    )
