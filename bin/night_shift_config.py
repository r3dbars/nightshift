"""Saved Night Shift config and quiet-hours helpers."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from night_shift_paths import CONFIG_DIR, CONFIG_PATH, cli_attr
from night_shift_setup import DEFAULT_PERMISSION, rows_by_name


CONFIG_SCHEMA_VERSION = 4


def load_config() -> dict:
    try:
        config = json.loads(cli_attr("CONFIG_PATH", CONFIG_PATH).read_text(encoding="utf-8"))
    except Exception:
        return {}
    # A prior opt-in was not a sandboxed-execution consent. Fail closed and
    # require the owner to opt in again through a repo profile.
    if config.get("schema_version", 0) < CONFIG_SCHEMA_VERSION:
        preferences = config.setdefault("preferences", {})
        if preferences.get("execute_drafts"):
            preferences["execute_drafts"] = False
            preferences["execution_reconsent_required"] = True
        config["schema_version"] = CONFIG_SCHEMA_VERSION
        config["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        save_config(config)
    return config


def save_config(config: dict) -> None:
    cli_attr("CONFIG_DIR", CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    cli_attr("CONFIG_PATH", CONFIG_PATH).write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def config_value(config: dict, key: str, default=None):
    if key in config:
        return config.get(key, default)
    if key == "repo":
        return config.get("project", {}).get("repo", default)
    if key in {
        "wake_goal",
        "privacy_route",
        "permission",
        "mode",
        "stop",
        "project_private",
        "guidance",
        "goal_text",
        "power",
        "scope",
        "active_days",
        "max_repos",
        "priority_repos",
        "quiet_hours",
        "execute_drafts",
        "run_checks",
        "run_e2e",
        "allow_cloud_reasoning",
        "allow_remote_lan_worker",
        "allow_draft_prs",
    }:
        return config.get("preferences", {}).get(key, default)
    if key in {"local_url", "local_model", "windows_url", "windows_model"}:
        return config.get("legacy", {}).get(key, default)
    return default


def parse_quiet_hours(value: str | None) -> tuple[int, int] | None:
    match = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*", value or "")
    if not match:
        return None
    start_hour, start_minute, end_hour, end_minute = (int(item) for item in match.groups())
    if any(hour > 23 for hour in (start_hour, end_hour)) or any(minute > 59 for minute in (start_minute, end_minute)):
        return None
    return start_hour * 60 + start_minute, end_hour * 60 + end_minute


def normalize_quiet_hours(value: str | None) -> str:
    parsed = parse_quiet_hours(value)
    if parsed is None:
        return ""
    start, end = parsed
    return f"{start // 60:02d}:{start % 60:02d}-{end // 60:02d}:{end % 60:02d}"


def quiet_hours_active(value: str | None, now: datetime | None = None) -> bool:
    parsed = parse_quiet_hours(value)
    if parsed is None:
        return False
    start, end = parsed
    current = now or datetime.now()
    minute = current.hour * 60 + current.minute
    if start == end:
        return True
    return start <= minute < end if start < end else minute >= start or minute < end


def configured_scope(config: dict) -> str:
    explicit = config.get("preferences", {}).get("scope") if config else None
    if explicit in {"current", "github-recent"}:
        return explicit
    # Existing installations were configured for one repo. Widening their
    # unattended scope requires a new setup confirmation.
    return "current" if config else "github-recent"


def recommended_start_preferences(saved: dict, rows: list[tuple[str, str, str]]) -> dict:
    """Choose safe, useful defaults so the normal setup needs one consent."""
    by_name = rows_by_name(rows)
    github_ready = by_name.get("gh-auth", ("", ""))[0] == "GREEN"
    saved_privacy = config_value(saved, "privacy_route", "")
    privacy_route = saved_privacy or (
        "mac-and-lan"
        if by_name.get("windows-worker", ("", ""))[0] == "GREEN"
        else "mac-only"
    )
    return {
        "wake_goal": config_value(saved, "wake_goal", "chores"),
        "privacy_route": privacy_route,
        "permission": config_value(saved, "permission", DEFAULT_PERMISSION),
        "mode": config_value(saved, "mode", "night-shift"),
        "stop": config_value(saved, "stop", "8h"),
        "scope": configured_scope(saved) if saved else ("github-recent" if github_ready else "current"),
    }

