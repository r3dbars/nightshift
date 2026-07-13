from __future__ import annotations


DEFAULT_MODE = "night-shift"


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
        "draft-local": "Draft local patch plans and issue candidates, but do not push",
        "draft-prs": "Prepare local patch candidates for review, but do not push or merge",
    }.get(permission, permission)


def autonomy_copy(permission: str) -> str:
    return {
        "brief": "Read-only. Make a brief and a ranked queue.",
        "draft-local": "More helpful. Draft exact local patch plans, tests, and issue candidates.",
        "draft-prs": "Most autonomous. Prepare local candidates only after the repo owner enables its sandbox profile.",
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
    execute_drafts = bool(prefs.get("execute_drafts", False))
    allow_draft_prs = bool(prefs.get("allow_draft_prs", False))
    stop = prefs.get("stop", "morning")
    wake_goal = prefs.get("wake_goal", "brief")
    privacy_route = prefs.get("privacy_route", "mac-only")
    tools = detected_tools(rows, privacy_route) or ["no worker AI found yet; planning brief only"]
    scope = prefs.get("scope", "github-recent")
    priority_repos = [str(item) for item in (prefs.get("priority_repos") or []) if str(item).strip()]
    quiet_hours = str(prefs.get("quiet_hours") or "").strip()
    patch_plan = (
        "Make test-gated patches in disposable copies"
        if execute_drafts
        else "Prepare reviewable plans without changing code"
    )
    publication = (
        "May open test-passed draft PRs; never merges them"
        if allow_draft_prs
        else "Keeps all work local; does not push"
    )
    lines = [
        "Night Shift preview", "", f"Project: {repo}", "", "Tonight:",
        "- Scan your recently active GitHub repos" if scope == "github-recent" else "- Scan this project",
        *([f"- Prioritize: {', '.join(priority_repos)}"] if priority_repos else []),
        *([f"- Stay quiet during {quiet_hours}"] if quiet_hours else []),
        f"- Use {', '.join(tools)}",
        f"- Look for {wake_goal_label(wake_goal).lower()}",
        f"- Use {mode_label(mode).lower()} effort and {stop_label(stop).lower()}",
        f"- {patch_plan}",
        "- Leave a short morning brief with proof and next steps",
        "", "Safety:",
        f"- {publication}",
        "- Never edits this checkout, merges, releases, deploys, or changes credentials",
        "- Never deletes or reorganizes your files, changes billing, or changes repo visibility",
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
        for key in ("allow_cloud_reasoning", "allow_draft_prs", "allow_remote_lan_worker", "execute_drafts"):
            if preferences.get(key) is False:
                preferences.pop(key)
        if "preferences" in normalized:
            normalized["preferences"] = preferences
        return normalized

    return comparable(saved) != comparable(proposed)
