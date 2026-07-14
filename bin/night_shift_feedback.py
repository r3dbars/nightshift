"""Turn explicit morning feedback into bounded pre-model task preferences."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile


CLARITY_VALUES = {"clear", "confusing"}
EFFORT_VALUES = {"quick", "some-work", "too-much"}
HUMAN_OUTCOME_VALUES = {"accepted", "revised", "rejected"}


FAMILY_PREFIXES = (
    "changed-file-proof",
    "docs-command-check",
    "failed-ci",
    "issue",
    "pr",
    "source-map",
    "test-contract-map",
)


def append_feedback_event(path: Path, event: dict) -> None:
    """Append one local feedback event without exposing prior votes to interruption."""
    try:
        existing = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        existing = ""
    prefix = existing if not existing or existing.endswith("\n") else existing + "\n"
    content = prefix + json.dumps(event, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
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


def task_family(slug: str) -> str:
    value = str(slug or "task").strip().lower()
    for prefix in FAMILY_PREFIXES:
        if value == prefix or value.startswith(prefix + "-"):
            return prefix
    return re.sub(r"(?:-\d+)+$", "", value) or "task"


def latest_feedback_events(events: list[dict]) -> list[dict]:
    """Return one current verdict per exact candidate, preserving last-write order."""
    latest: dict[tuple, dict] = {}
    for index, event in enumerate(events):
        if event.get("ledger") and event.get("rank"):
            candidate = f"displayed:{event['ledger']}:{event['rank']}"
        else:
            candidate = event.get("fingerprint") or event.get("key")
        identity = (
            event.get("repo"), event.get("family"), candidate or f"legacy:{index}",
        )
        latest[identity] = event
    return list(latest.values())


def feedback_quality_snapshot(events: list[dict], repo: str = "") -> dict[str, int]:
    """Summarize optional local clarity and review-effort signals."""
    current = latest_feedback_events(
        [event for event in events if not repo or event.get("repo") == repo]
    )
    return {
        "clear": sum(event.get("clarity") == "clear" for event in current),
        "confusing": sum(event.get("clarity") == "confusing" for event in current),
        "quick": sum(event.get("effort") == "quick" for event in current),
        "some-work": sum(event.get("effort") == "some-work" for event in current),
        "too-much": sum(event.get("effort") == "too-much" for event in current),
        "accepted": sum(event.get("human_outcome") == "accepted" for event in current),
        "revised": sum(event.get("human_outcome") == "revised" for event in current),
        "rejected": sum(event.get("human_outcome") == "rejected" for event in current),
    }


def feedback_delay_seconds(reviewed_at: str, feedback_at: str) -> float | None:
    """Return elapsed seconds between viewing a brief and voting, when valid."""
    try:
        def parse(value: str) -> datetime:
            parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)

        viewed = parse(reviewed_at)
        voted = parse(feedback_at)
    except (TypeError, ValueError, OverflowError):
        return None
    delay = (voted - viewed).total_seconds()
    if delay < 0:
        return None
    return round(delay, 3)


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
        event.get("ledger"), event.get("rank"), event.get("fingerprint"), event.get("verdict"),
        event.get("clarity"), event.get("effort"), event.get("human_outcome"),
    )
    return not any(
        (
            row.get("ledger"), row.get("rank"), row.get("fingerprint"), row.get("verdict"),
            row.get("clarity"), row.get("effort"), row.get("human_outcome"),
        )
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
