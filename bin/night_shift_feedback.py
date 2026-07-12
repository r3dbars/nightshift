"""Turn explicit morning feedback into bounded pre-model task preferences."""
from __future__ import annotations

import re


FAMILY_PREFIXES = (
    "changed-file-proof",
    "docs-command-check",
    "failed-ci",
    "issue",
    "pr",
    "source-map",
    "test-contract-map",
)


def task_family(slug: str) -> str:
    value = str(slug or "task").strip().lower()
    for prefix in FAMILY_PREFIXES:
        if value == prefix or value.startswith(prefix + "-"):
            return prefix
    return re.sub(r"-\d+$", "", value) or "task"


def feedback_score(events: list[dict], repo: str, family: str) -> tuple[int, int, int]:
    useful = 0
    not_useful = 0
    for event in events:
        if event.get("repo") != repo or event.get("family") != family:
            continue
        if event.get("verdict") == "useful":
            useful += 1
        elif event.get("verdict") == "not-useful":
            not_useful += 1
    adjustment = max(-40, min(50, useful * 25 - not_useful * 20))
    return adjustment, useful, not_useful


def apply_task_feedback(
    tasks: list[dict], events: list[dict], repo: str, mode: str
) -> tuple[list[dict], list[dict]]:
    ranked: list[dict] = []
    skipped: list[dict] = []
    for task in tasks:
        row = dict(task)
        family = task_family(str(row.get("slug") or ""))
        adjustment, useful, not_useful = feedback_score(events, repo, family)
        row["feedback_family"] = family
        row["feedback_adjustment"] = adjustment
        if mode != "afterburner" and not_useful >= 2 and not_useful > useful:
            skipped.append(
                {
                    "slug": row.get("slug", ""),
                    "category": "feedback",
                    "reason": f"task family '{family}' was marked not useful {not_useful} times",
                }
            )
            continue
        ranked.append(row)
    ranked.sort(
        key=lambda row: (
            -(
                int(row.get("selection_priority") or row.get("ladder_priority") or 0)
                + int(row.get("feedback_adjustment") or 0)
            ),
            str(row.get("slug") or ""),
        )
    )
    return ranked, skipped
