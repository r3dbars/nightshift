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


def latest_feedback_events(events: list[dict]) -> list[dict]:
    """Return one current verdict per exact candidate, preserving last-write order."""
    latest: dict[tuple, dict] = {}
    for index, event in enumerate(events):
        candidate = event.get("fingerprint") or event.get("key")
        if not candidate and event.get("ledger") and event.get("rank"):
            candidate = f"{event['ledger']}:{event['rank']}"
        identity = (
            event.get("repo"), event.get("family"), candidate or f"legacy:{index}",
        )
        latest[identity] = event
    return list(latest.values())


def feedback_score(events: list[dict], repo: str, family: str) -> tuple[int, int, int]:
    useful = 0
    not_useful = 0
    for event in latest_feedback_events(events):
        if event.get("repo") != repo or event.get("family") != family:
            continue
        if event.get("verdict") == "useful":
            useful += 1
        elif event.get("verdict") == "not-useful":
            not_useful += 1
    adjustment = max(-40, min(50, useful * 25 - not_useful * 20))
    return adjustment, useful, not_useful


def should_record_feedback_event(existing: list[dict], event: dict) -> bool:
    identity = (
        event.get("ledger"), event.get("rank"), event.get("fingerprint"), event.get("verdict")
    )
    return not any(
        (row.get("ledger"), row.get("rank"), row.get("fingerprint"), row.get("verdict"))
        == identity
        for row in existing
    )


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


def apply_review_outcomes(
    tasks: list[dict], outcomes: list[dict], repo: str, source_ref: str
) -> tuple[list[dict], list[dict]]:
    """Apply validated review decisions only to the exact candidate revision."""
    latest: dict[str, dict] = {}
    for outcome in outcomes:
        fingerprint = str(outcome.get("fingerprint") or "")
        if (
            fingerprint
            and outcome.get("valid_review") is True
            and outcome.get("repo") == repo
            and outcome.get("source_ref") == source_ref
            and outcome.get("verdict") in {"CONFIRMED", "REJECTED", "NEEDS_INFO"}
        ):
            latest[fingerprint] = outcome
    ready: list[dict] = []
    skipped: list[dict] = []
    for task in tasks:
        row = dict(task)
        outcome = latest.get(str(row.get("fingerprint") or ""))
        if not outcome:
            ready.append(row)
            continue
        verdict = outcome["verdict"]
        row["review_outcome"] = verdict
        if verdict == "REJECTED":
            skipped.append({
                "fingerprint": row.get("fingerprint", ""),
                "slug": row.get("slug", ""),
                "category": "review-outcome",
                "reason": "independent review rejected this exact candidate at this revision",
            })
            continue
        if (
            verdict == "CONFIRMED"
            and outcome.get("utility_valid") is True
            and outcome.get("utility_schema") == 2
            and outcome.get("ready_for_implementation") is True
        ):
            row["selection_priority"] = int(
                row.get("selection_priority") or row.get("ladder_priority") or 0
            ) + 30
        ready.append(row)
    ready.sort(
        key=lambda row: (
            -(
                int(row.get("selection_priority") or row.get("ladder_priority") or 0)
                + int(row.get("feedback_adjustment") or 0)
            ),
            str(row.get("slug") or ""),
        )
    )
    return ready, skipped


def should_record_review_outcome(existing: list[dict], outcome: dict) -> bool:
    identity = (
        outcome.get("ledger"), outcome.get("item"), outcome.get("fingerprint"),
        outcome.get("source_ref"), outcome.get("verdict"),
        outcome.get("utility_schema"), outcome.get("ready_for_implementation"),
    )
    return not any(
        (
            row.get("ledger"), row.get("item"), row.get("fingerprint"),
            row.get("source_ref"), row.get("verdict"),
            row.get("utility_schema"), row.get("ready_for_implementation"),
        ) == identity
        for row in existing
    )
