from __future__ import annotations


DEFAULT_MODE = "night-shift"
DEFAULT_PERMISSION = "draft-prs"


def autonomy_flags(permission: str) -> dict[str, bool]:
    """Collapse three implementation flags into one user-facing choice."""
    return {
        "execute_drafts": permission in {"draft-local", "draft-prs"},
        "run_checks": permission in {"draft-local", "draft-prs"},
        "run_e2e": permission == "draft-prs",
        "allow_draft_prs": permission == "draft-prs",
    }


def rows_by_name(rows: list[tuple[str, str, str]]) -> dict[str, tuple[str, str]]:
    return {name: (state, message) for name, state, message in rows}


def row_state(rows: list[tuple[str, str, str]], name: str) -> str:
    return rows_by_name(rows).get(name, ("", ""))[0]


def detected_tools(rows: list[tuple[str, str, str]], privacy_route: str = "mac-only") -> list[str]:
    by_name = rows_by_name(rows)
    tools = []
    if by_name.get("local-models", ("", ""))[0] == "GREEN" and by_name.get("local-chat", ("", ""))[0] == "GREEN":
        tools.append("local Mac AI")
    if privacy_route == "mac-and-lan" and by_name.get("windows-worker", ("", ""))[0] == "GREEN":
        tools.append("another computer")
    if by_name.get("gh-auth", ("", ""))[0] == "GREEN":
        tools.append("GitHub CLI for repo context")
    return tools


def mode_label(mode: str) -> str:
    return {"quiet": "Quiet", "night-shift": "Normal", "afterburner": "Afterburner"}.get(mode, mode)


def wake_goal_label(goal: str) -> str:
    return {
        "brief": "A short morning brief only",
        "chores": "Ranked repo chores and test ideas",
        "draft-prs": "Draft PR candidates, but only after checks",
    }.get(goal, goal)


def privacy_route_label(route: str) -> str:
    return {
        "mac-only": "Keep repo context on this Mac",
        "mac-and-lan": "Use this Mac plus my other AI computer",
        "cloud-ok": "Cloud coding subscriptions are okay for hard questions",
    }.get(route, route)


def permission_label(permission: str) -> str:
    return {
        "brief": "Read only and make a morning brief",
        "draft-local": "Make tested changes in disposable copies, but keep them local",
        "draft-prs": "Open tested draft PRs for review; never merge",
    }.get(permission, permission)


def autonomy_copy(permission: str) -> str:
    return {
        "brief": "Read-only. Make a brief and a ranked queue.",
        "draft-local": "Hands-on. Make small tested changes in disposable copies and keep them local.",
        "draft-prs": "Autopilot. Make small tested changes and open draft PRs for review; never merge.",
    }.get(permission, "Read-only. Make a brief and a ranked queue.")


def stop_label(stop: str) -> str:
    return {
        "morning": "Stop when I come back",
        "2h": "Stop after 2 hours",
        "6h": "Stop after 6 hours",
        "8h": "Stop after 8 hours",
        "10h": "Stop after 10 hours",
    }.get(stop, stop)


def mode_counts(
    mode: str,
    mode_defaults: dict,
    rows: list[tuple[str, str, str]] | None = None,
    privacy_route: str = "mac-only",
) -> str:
    defaults = mode_defaults.get(mode, mode_defaults[DEFAULT_MODE])
    if rows is None:
        return "unique task batches, deepest useful work first"
    by_name = rows_by_name(rows)
    local = defaults["local"] if (
        by_name.get("local-models", ("", ""))[0] == "GREEN"
        and by_name.get("local-chat", ("", ""))[0] == "GREEN"
    ) else 0
    windows = defaults["windows"] if (
        privacy_route == "mac-and-lan" and by_name.get("windows-worker", ("", ""))[0] == "GREEN"
    ) else 0
    if local and windows:
        return "unique task batches on this Mac and the other computer"
    if local:
        return "unique task batches on this Mac"
    if windows:
        return "unique task batches on the other computer"
    return "planning brief only until worker AI is reachable"


def start_preview(config: dict, rows: list[tuple[str, str, str]], mode_defaults: dict) -> str:
    repo = config.get("project", {}).get("repo", config.get("repo", "unknown"))
    prefs = config.get("preferences", config)
    mode = prefs.get("mode", DEFAULT_MODE)
    permission = prefs.get("permission", "brief")
    execute_drafts = bool(prefs.get("execute_drafts", False)) and permission != "brief"
    allow_draft_prs = bool(prefs.get("allow_draft_prs", False))
    run_e2e = bool(prefs.get("run_e2e", False))
    run_checks = bool(prefs.get("run_checks", False))
    stop = prefs.get("stop", "morning")
    wake_goal = prefs.get("wake_goal", "brief")
    privacy_route = prefs.get("privacy_route", "mac-only")
    by_name = rows_by_name(rows)
    local_worker_ready = (
        by_name.get("local-models", ("", ""))[0] == "GREEN"
        and by_name.get("local-chat", ("", ""))[0] == "GREEN"
    )
    windows_worker_ready = (
        privacy_route == "mac-and-lan"
        and by_name.get("windows-worker", ("", ""))[0] == "GREEN"
    )
    worker_ready = local_worker_ready or windows_worker_ready
    tools = detected_tools(rows, privacy_route)
    scope = prefs.get("scope", "github-recent")
    priority_repos = [str(item) for item in (prefs.get("priority_repos") or []) if str(item).strip()]
    quiet_hours = str(prefs.get("quiet_hours") or "").strip()
    patch_plan = (
        "Make small test-gated code, test, E2E, docs, and cleanup changes in disposable copies"
        if execute_drafts and worker_ready
        else "Make a planning brief tonight; hands-on work starts when worker AI is reachable"
        if execute_drafts
        else "Prepare reviewable plans without changing code"
    )
    publication = (
        "Open only test-passed draft PRs for review; never merge them"
        if allow_draft_prs and worker_ready
        else "No draft PR will be opened tonight because worker AI is unavailable"
        if allow_draft_prs
        else "Keeps all work local; does not push"
    )
    verification = (
        "- Keep approved checks ready; no check or patch starts until worker AI is reachable"
        if not worker_ready
        else "- Run one approved deterministic check and one approved E2E/smoke check per repo in isolated no-network runners"
        if run_checks and run_e2e
        else "- Run one already-approved deterministic check per repo in the isolated no-network runner"
        if run_checks
        else "- Run one already-approved E2E/smoke check per repo in the isolated no-network runner"
        if run_e2e
        else "- Notice tests and E2E surfaces; never run an unapproved command"
    )
    tool_line = (
        f"- Use {', '.join(tools)}"
        if tools
        else "- Worker AI is not reachable yet"
    )
    lines = [
        "Night Shift preview", "", f"Project: {repo}", "", "Tonight:",
        "- Scan your recently active GitHub repos" if scope == "github-recent" else "- Scan this project",
        *([f"- Prioritize: {', '.join(priority_repos)}"] if priority_repos else []),
        *([f"- Stay quiet during {quiet_hours}"] if quiet_hours else []),
        tool_line,
        f"- Look for {wake_goal_label(wake_goal).lower()}",
        f"- Use {mode_label(mode).lower()} effort and {stop_label(stop).lower()}",
        verification,
        f"- {patch_plan}",
        "- Leave a short morning brief with proof and next steps",
        "", "Safety:",
        f"- {publication}",
        "- Will never edit this checkout, merge, release, deploy, or change credentials",
        "- Will never delete or reorganize your files, change billing, or change repo visibility",
        f"- {privacy_route_label(privacy_route)}",
        "", "Change these choices anytime with `night-shift start --advanced`.",
        f"If setup fails, run `night-shift doctor --repo {repo}`.",
    ]
    return "\n".join(lines)


def setup_has_changed(saved: dict, proposed: dict) -> bool:
    if not saved:
        return True

    def comparable(value: dict) -> dict:
        normalized = {key: item for key, item in value.items() if key != "updated_at"}
        preferences = dict(normalized.get("preferences") or {})
        # Missing consent is deliberately equivalent to explicit denial. Adding
        # a new fail-closed flag must not make a repeat launch look like setup.
        for key in ("allow_cloud_reasoning", "allow_draft_prs", "allow_remote_lan_worker", "execute_drafts", "run_e2e", "run_checks"):
            if preferences.get(key) is False:
                preferences.pop(key)
        if "preferences" in normalized:
            normalized["preferences"] = preferences
        return normalized

    return comparable(saved) != comparable(proposed)
