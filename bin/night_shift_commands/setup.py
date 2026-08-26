"""Night Shift command handlers. Names resolve from night_shift_cli at call time."""
from __future__ import annotations

from night_shift_commands._bind import bind_cli


@bind_cli
def command_doctor(args) -> int:
    apply_compute_overrides(args)
    overall, rows = doctor_checks(args.repo, run_smoke=args.smoke)
    print(f"NIGHTSHIFT_DOCTOR: {overall}")
    for name, state, message in rows:
        print(f"{state}\t{name}\t{message}")
    advice = doctor_advice(rows)
    if advice:
        print("")
        print("Next steps:")
        for item in advice:
            print(f"- {item}")
    if overall == "RED":
        return 1
    return 0

@bind_cli
def command_health(args) -> int:
    config = load_config()
    repo = args.repo or config_value(config, "repo")
    overall, rows = doctor_checks(repo, run_smoke=False, allow_fetch=False)
    latest = latest_ledger()
    metrics = parse_json_text((latest / "outcome-metrics.json").read_text(encoding="utf-8"), {}) if latest and (latest / "outcome-metrics.json").exists() else {}
    attempts = latest_attempts(TASK_ATTEMPTS_PATH)
    active = active_autopilot()
    print(f"NIGHTSHIFT_HEALTH: {overall}")
    print(f"- Controller: {'running pid=' + str(active.get('pid')) if active else 'not running'}")
    print(f"- Latest ledger: {latest or 'none'}")
    print(f"- Ledger storage: {round(directory_size(OVERNIGHT_ROOT) / 1024**2, 1)} MB")
    reclaimable = cleanup_candidates(OVERNIGHT_ROOT, days=21)
    reclaimable_bytes = sum(directory_size(path) for path in reclaimable)
    print(f"- Reclaimable reviewed ledgers: {len(reclaimable)} ({round(reclaimable_bytes / 1024**2, 1)} MB; use `night-shift clean --apply`)")
    print(f"- Durable task fingerprints: {len(attempts)}")
    if metrics:
        print(
            f"- Latest outcomes: attempted={metrics.get('attempted', 0)} "
            f"candidates={metrics.get('accepted_candidates', 0)} "
            f"verified={metrics.get('verified_drafts', 0)} "
            f"rejected={metrics.get('rejected', 0)} tokens~={metrics.get('estimated_tokens', 0)} "
            f"tokens/verified~={metrics.get('tokens_per_verified_draft', 0)}"
        )
    outcome_summary = outcome_ledger_summary(load_repo_outcomes(REPO_OUTCOMES_PATH))
    print(
        f"- Outcome ledger: runs={outcome_summary['runs']} "
        f"verified_drafts={outcome_summary['verified_drafts']} "
        f"candidate_only={outcome_summary['candidate_only_candidates']} "
        f"tokens/verified~={outcome_summary['tokens_per_verified_draft']} "
        f"useful_verified_votes={outcome_summary['useful_verified_feedback']} "
        f"useful_candidate_votes={outcome_summary['useful_candidate_feedback']} "
        f"accepted/revised/rejected_verified="
        f"{outcome_summary['accepted_verified_outcomes']}/"
        f"{outcome_summary['revised_verified_outcomes']}/"
        f"{outcome_summary['rejected_verified_outcomes']} "
        f"hosted_green_drafts={outcome_summary['hosted_green_draft_prs']}"
    )
    feedback = load_feedback()
    current_feedback = latest_feedback_events(feedback)
    useful = sum(row.get("verdict") == "useful" for row in current_feedback)
    not_useful = sum(row.get("verdict") == "not-useful" for row in current_feedback)
    print(
        f"- Learning: current_preferences={len(current_feedback)} useful={useful} "
        f"not_useful={not_useful} history_events={len(feedback)}"
    )
    for name in ("local-chat", "windows-worker", "windows-chat", "repo-profile", "sandbox-provider", "sandbox"):
        state, message = rows_by_name(rows).get(name, ("INFO", "not checked"))
        print(f"- {name}: {state} | {message}")
    return 1 if overall == "RED" else 0

@bind_cli
def command_brain_intake(args) -> int:
    """Triage new ClaudeBrain raw files without editing the vault's durable pages."""
    saved = load_config()
    local_url = (
        getattr(args, "local_url", None)
        or os.environ.get("MAESTRO_LOCAL_BASE_URL")
        or config_value(saved, "local_url")
        or DEFAULT_LOCAL_URL
    )
    local_model = (
        getattr(args, "local_model", None)
        or os.environ.get("MAESTRO_LOCAL_MODEL")
        or config_value(saved, "local_model")
        or DEFAULT_LOCAL_MODEL
    )

    def call_model(prompt: str, model: str) -> str:
        data = retry_transient(
            post_url_json,
            f"{local_url.rstrip('/')}/chat/completions",
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 900,
                "temperature": 0,
            },
            timeout=max(20, getattr(args, "timeout", 90)),
        )
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise RuntimeError("local model returned no message content")
        return content

    try:
        result = run_brain_intake(
            Path(args.vault),
            state_path=CONFIG_DIR / "claudebrain-raw-state.json",
            local_model=local_model,
            max_files=args.max_files,
            max_chars=args.max_chars,
            max_bytes=args.max_bytes,
            include_legacy=args.include_legacy,
            call_model=call_model,
        )
    except ValueError as exc:
        print(f"NIGHTSHIFT_BRAIN: RED | {exc}")
        return 2
    print(
        f"NIGHTSHIFT_BRAIN: {result['status']} | discovered={result['discovered']} "
        f"processed={result['processed']} blocked={result['blocked']}"
    )
    if result.get("packet"):
        print(f"Triage packet: {result['packet']}")
    print(f"State: {result['state']}")
    return 0 if result["status"] in {"GREEN", "NO_WORK"} else 1

@bind_cli
def command_sandbox(args) -> int:
    status = detect_sandbox(run_cmd)
    if not args.build_runner:
        print(f"NIGHTSHIFT_SANDBOX: {'GREEN' if status.available else 'YELLOW'} | {status.detail}")
        if not status.available:
            print("Execution stays disabled. Install/start a rootless Docker or Podman provider, then run `night-shift sandbox --build-runner`.")
        return 0 if status.available else 1
    ok, detail = build_runner_image(run_cmd)
    if not ok:
        print(f"NIGHTSHIFT_SANDBOX: YELLOW | {detail}")
        return 1
    print("NIGHTSHIFT_SANDBOX: GREEN | reviewed local runner built")
    print("Add this image value to a reviewed .night-shift.json profile:")
    print(f'  "image": "{detail}"')
    return 0

@bind_cli
def command_trust_repo(args) -> int:
    repo = require_git_repo(args.repo)
    if not repo:
        return 1
    remote = repo_remote(repo)
    slug = repo_slug(repo)
    if not remote or not slug or "/" not in slug:
        print("NIGHTSHIFT_TRUST_REPO: RED | repo needs an origin GitHub remote")
        return 1
    owner = slug.split("/", 1)[0].lower()
    viewer = (
        run_cmd(["gh", "api", "user", "--jq", ".login"], timeout=30)
        if shutil.which("gh")
        else CmdResult("gh", 1, "", "gh unavailable")
    )
    if viewer.rc != 0 or viewer.stdout.strip().lower() != owner:
        print("NIGHTSHIFT_TRUST_REPO: RED | GitHub ownership could not be proven for this repo")
        return 1
    remote_repo = run_cmd(
        ["gh", "repo", "view", slug, "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
        timeout=30,
    )
    if remote_repo.rc != 0 or remote_repo.stdout.strip().lower() != slug.lower():
        print("NIGHTSHIFT_TRUST_REPO: RED | the exact GitHub repository identity could not be verified")
        return 1
    scan = repo_signal_scan(repo)
    commands = trust_repo_commands(repo, scan, getattr(args, "include_e2e", False))
    if not commands:
        print("NIGHTSHIFT_TRUST_REPO: RED | no safe deterministic verification command was detected")
        return 1
    candidate_paths = [
        *scan.get("source_files", []),
        *scan.get("test_files", []),
        *scan.get("e2e_files", []),
        *scan.get("doc_files", []),
    ]
    allowed_paths = list(dict.fromkeys(
        path.split("/", 1)[0] if "/" in path else path
        for path in candidate_paths
        if path
    ))[:20]
    if not allowed_paths:
        allowed_paths = [
            path for path in ("src", "lib", "app", "tests", "test", "Sources", "Tests")
            if (repo / path).exists()
        ]
    print("NIGHTSHIFT_TRUST_REPO: REVIEW")
    print(f"- Repo: {slug}")
    print(f"- Remote: {remote}")
    print(f"- Verification: {command_display(commands[0])}")
    if len(commands) > 1:
        print(f"- Optional E2E verification: {command_display(commands[1])}")
    print(f"- Writable paths in disposable worktrees only: {', '.join(allowed_paths)}")
    print("- Original checkout: read-only")
    print("- GitHub writes: disabled by this approval")
    if not args.apply:
        print("Nothing was saved. Re-run with --apply to review one consent prompt.")
        return 0
    if not args.yes:
        answer = input("Save this isolated-execution approval? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("NIGHTSHIFT_TRUST_REPO: YELLOW | approval not saved")
            return 1
    ok, image = build_runner_image(run_cmd)
    if not ok:
        print(f"NIGHTSHIFT_TRUST_REPO: YELLOW | {image}")
        return 1
    profile = {
        "version": 1,
        "trust": "owned",
        "execution": "sandbox-only",
        "image": image,
        "commands": commands,
        "allowed_paths": allowed_paths,
        "protected_paths": sorted(PROTECTED_PATHS),
        "limits": {"cpu": 2, "memory_mb": 2048, "pids": 128, "seconds": 900},
    }
    parsed_profile, profile_detail = parse_repo_profile(profile)
    if not parsed_profile:
        print(f"NIGHTSHIFT_TRUST_REPO: RED | generated approval is invalid: {profile_detail}")
        return 1
    dependency_source = dependency_source_for_repo(
        repo, shared_dependency_cache_root(), remote, image,
    )
    if should_prepare_runner_dependencies(repo, getattr(args, "prepare_dependencies", False)):
        cache_dir = dependency_cache_path(shared_dependency_cache_root(), remote, image, repo / "package-lock.json")
        prepared, dependency_detail = prepare_node_dependencies(
            repo, cache_dir, remote, image, run_cmd,
        )
        if not prepared:
            print(f"NIGHTSHIFT_TRUST_REPO: YELLOW | runner-native dependency setup failed: {dependency_detail}")
            print("Nothing was saved. Night Shift stays analysis-only for this repo.")
            return 1
        dependency_source = cache_dir / "node_modules"
        print(f"- Runner-native dependencies: prepared at {dependency_source}")
    elif dependency_source is None and (repo / "node_modules").is_dir():
        dependency_source = repo / "node_modules"
    preflight = run_cmd(
        sandbox_command(repo, tuple(commands[0]), parsed_profile, dependency_source),
        cwd=repo,
        timeout=parsed_profile.max_seconds,
    )
    preflight_state, preflight_detail = verification_preflight(preflight, tuple(commands[0]))
    if preflight_state == "BLOCKED":
        print(f"NIGHTSHIFT_TRUST_REPO: YELLOW | verification cannot run in the isolated runner: {preflight_detail}")
        print("Nothing was saved. Night Shift stays analysis-only for this repo.")
        return 1
    repeated = run_cmd(
        sandbox_command(repo, tuple(commands[0]), parsed_profile, dependency_source),
        cwd=repo,
        timeout=parsed_profile.max_seconds,
    )
    repeated_state, repeated_detail = verification_preflight(repeated, tuple(commands[0]))
    if repeated_state == "BLOCKED":
        print(f"NIGHTSHIFT_TRUST_REPO: YELLOW | repeated verification was blocked: {repeated_detail}")
        print("Nothing was saved. Night Shift stays analysis-only for this repo.")
        return 1
    if repeated_state != preflight_state:
        print("NIGHTSHIFT_TRUST_REPO: YELLOW | verification changed result across two isolated runs")
        print("Nothing was saved. Night Shift stays analysis-only for this repo.")
        return 1
    if preflight_state == "FAILING":
        signatures = [
            test_failure_signature(result.stdout + "\n" + result.stderr)
            for result in (preflight, repeated)
        ]
        if not all(signatures) or len(set(signatures)) != 1:
            print("NIGHTSHIFT_TRUST_REPO: YELLOW | the same identifiable test failure did not reproduce twice")
            print("Nothing was saved. Night Shift stays analysis-only for this repo.")
            return 1
    try:
        path = save_approval(REPO_APPROVALS_ROOT, remote, slug, profile)
    except OSError as exc:
        print(f"NIGHTSHIFT_TRUST_REPO: RED | could not save approval safely: {exc}")
        return 1
    loaded, detail = load_repo_profile(repo)
    if not loaded or not loaded.may_execute:
        path.unlink(missing_ok=True)
        print(f"NIGHTSHIFT_TRUST_REPO: RED | saved approval failed validation: {detail}")
        return 1
    suffix = (
        "verification passed twice"
        if preflight_state == "PASS"
        else f"the same verification failure reproduced twice (rc={preflight.rc})"
    )
    print(f"NIGHTSHIFT_TRUST_REPO: GREEN | approval saved outside the repo at {path}; {suffix}")
    return 0

@bind_cli
def command_start(args) -> int:
    saved = {} if args.reset else load_config()
    first_run = not bool(saved)
    advanced = bool(getattr(args, "advanced", False))
    apply_compute_overrides(args)

    if not is_interactive() and not args.yes and not args.dry_run and not args.setup_only:
        print("NIGHTSHIFT_START: RED | I need a keyboard for the setup questions.")
        print("Try: night-shift start --repo /path/to/project --yes --dry-run")
        print("Or run: night-shift start from a normal terminal window.")
        return 2

    repo, repo_error = resolve_start_repo(args, saved)
    if repo_error:
        print(f"NIGHTSHIFT_START: RED | {repo_error}")
        return 2

    if first_run and not args.yes and is_interactive():
        print_first_run_intro()
    if advanced and not args.yes and is_interactive():
        repo = ask_text("Which project should Night Shift look at?", repo)
    elif not repo:
        print("NIGHTSHIFT_START: RED | pass --repo /path/to/project or run from inside a git repo")
        return 2

    root = repo_root(repo)
    repo_check = run_cmd(["git", "-C", root, "rev-parse", "--show-toplevel"], timeout=20) if root else None
    if not repo_check or repo_check.rc != 0:
        print(f"NIGHTSHIFT_START: RED | not a Git repository: {Path(repo).expanduser()}")
        return 2
    repo_text = str(Path(repo_check.stdout.strip()).resolve())

    print("")
    print("Give me a second to check what is ready on this computer...")
    overall, rows = doctor_checks(repo_text, run_smoke=False, allow_fetch=False)
    configured_windows = (
        args.windows_url
        or os.environ.get("WINDOWS_WORKER_BASE_URL")
        or config_value(saved, "windows_url", "")
    )
    requested_privacy = (
        args.privacy
        or config_value(saved, "privacy_route", "")
        or ("mac-and-lan" if configured_windows else "mac-only")
    )
    shown = set()
    for name, state, message in rows:
        if name in ("local-models", "local-chat", "windows-worker", "claude", "gh-auth", "repo", "power"):
            if name == "windows-worker" and requested_privacy != "mac-and-lan":
                continue
            friendly = friendly_setup_row(name, state, message)
            if friendly and friendly not in shown:
                print(f"- {friendly}")
                shown.add(friendly)

    detected_local = autodetect_local_server() if first_run and not args.local_url and not args.local_model else None
    local_url = (
        args.local_url
        or os.environ.get("MAESTRO_LOCAL_BASE_URL")
        or config_value(saved, "local_url")
        or (detected_local[0] if detected_local else DEFAULT_LOCAL_URL)
    )
    local_model = (
        args.local_model
        or os.environ.get("MAESTRO_LOCAL_MODEL")
        or config_value(saved, "local_model")
        or (detected_local[1] if detected_local and detected_local[1] else DEFAULT_LOCAL_MODEL)
    )
    windows_url = args.windows_url or os.environ.get("WINDOWS_WORKER_BASE_URL") or config_value(saved, "windows_url", "")
    windows_model = args.windows_model or os.environ.get("WINDOWS_WORKER_MODEL") or config_value(saved, "windows_model", DEFAULT_WINDOWS_MODEL)

    recommended = recommended_start_preferences(saved, rows)
    wake_goal = args.wake_goal or recommended["wake_goal"]
    privacy_route = args.privacy or recommended["privacy_route"]
    guidance = args.guidance or config_value(saved, "guidance", "scan")
    goal_text = args.goal if args.goal is not None else config_value(saved, "goal_text", "")
    if args.goal and not args.guidance:
        guidance = "goal"
    permission = args.permission or recommended["permission"]
    mode = args.mode or recommended["mode"]
    stop = args.stop_after or recommended["stop"]
    scope = args.scope or recommended["scope"]
    active_days = args.active_days or config_value(saved, "active_days", 14)
    max_repos = args.max_repos or config_value(saved, "max_repos", AUTOPILOT_DEFAULTS[mode]["repo_limit"])
    priority_repos = PortfolioEngine.normalize_priority_repos(config_value(saved, "priority_repos", []))
    quiet_hours = normalize_quiet_hours(config_value(saved, "quiet_hours", ""))
    preset = autonomy_flags(permission) if first_run or args.permission is not None else {}
    execute_drafts = bool(
        getattr(args, "execute_drafts", False)
        or config_value(saved, "execute_drafts", preset.get("execute_drafts", False))
    )
    run_e2e = bool(
        getattr(args, "run_e2e", False)
        or config_value(saved, "run_e2e", preset.get("run_e2e", False))
    )
    run_checks = bool(
        getattr(args, "run_checks", False)
        or config_value(saved, "run_checks", preset.get("run_checks", False))
    )
    allow_draft_prs = bool(
        getattr(args, "allow_draft_prs", False)
        or config_value(saved, "allow_draft_prs", False)
    )
    if permission != "draft-prs":
        allow_draft_prs = False
    if permission == "brief":
        execute_drafts = False
    project_private = "normal" if privacy_route == "cloud-ok" else "private"

    if advanced and not args.yes and is_interactive():
        scope = ask_choice(
            "Where should Night Shift look for useful work?",
            [
                ("github-recent", "My recently active GitHub repos, starting with this project"),
                ("current", "Only this project"),
            ],
            scope if scope in {"github-recent", "current"} else "github-recent",
        )
        priority_text = ask_text(
            "Any GitHub repos to prioritize? Use owner/repo, separated by commas, or press Enter for none",
            ", ".join(priority_repos),
        )
        priority_repos = PortfolioEngine.normalize_priority_repos(priority_text.split(","))
        quiet_hours = normalize_quiet_hours(ask_text(
            "When should Night Shift stay quiet? Use HH:MM-HH:MM, or press Enter for none",
            quiet_hours,
        ))
        wake_goal = ask_choice(
            "What would make tomorrow morning a win?",
            [
                ("brief", "A calm morning brief: what happened, what matters, what to do first"),
                ("chores", "A ranked hit list: bugs, tests, docs, and small safe chores"),
                ("draft-prs", "Tested draft PRs ready for review; Night Shift never merges"),
            ],
            wake_goal if wake_goal in {"brief", "chores", "draft-prs"} else "brief",
        )
        guidance = ask_choice(
            "What should Night Shift aim at first?",
            [
                ("scan", "Find the sharpest safe work for me"),
                ("goal", "I have one mission for tonight"),
                ("issues", "Use open issues and PRs as the map"),
            ],
            guidance if guidance in {"scan", "goal", "issues"} else "scan",
        )
        if guidance == "goal":
            goal_text = ask_text("In one sentence, what is tonight's mission?", goal_text or "Find the highest-value safe next task")

        privacy_route = ask_choice(
            "Where is repo context allowed to go tonight?",
            [
                ("mac-only", "Only this Mac: safest and private"),
                ("mac-and-lan", "This Mac plus my other AI computer on my network"),
                ("cloud-ok", "Cloud coding subscriptions are okay for hard questions"),
            ],
            privacy_route if privacy_route in {"mac-only", "mac-and-lan", "cloud-ok"} else "mac-only",
        )
        project_private = "normal" if privacy_route == "cloud-ok" else "private"

        if privacy_route in ("mac-only", "mac-and-lan") or args.local_url or args.local_model:
            local_url = ask_text("Mac local AI URL. Press Enter for LM Studio's usual address", local_url)
            local_model = ask_text("Mac local model name. Press Enter for the starter model", local_model)
        if privacy_route == "mac-and-lan":
            if not windows_url:
                print("I will check only the private devices your Mac already knows about.")
                print("This sends no repo information; it only asks known model-server ports for their model list.")
                discovered_workers = discover_lan_workers()
                if len(discovered_workers) == 1:
                    found = discovered_workers[0]
                    use_found = ask_yes_no(
                        f"I found {found['host']} with {found['model']}. Use this other computer?",
                        default=True,
                    )
                    if use_found:
                        windows_url = found["url"]
                        windows_model = found["model"]
                elif discovered_workers:
                    choices = [
                        (str(index), f"{item['host']} with {item['model']}")
                        for index, item in enumerate(discovered_workers, start=1)
                    ]
                    choices.append(("manual", "I will enter the address myself"))
                    selected = ask_choice(
                        "Which other computer should Night Shift use?",
                        choices,
                        "1",
                    )
                    if selected != "manual":
                        found = discovered_workers[int(selected) - 1]
                        windows_url = found["url"]
                        windows_model = found["model"]
            if not windows_url:
                windows_url = ask_text(
                    "I did not find one automatically. Other computer AI address, or press Enter to skip",
                    "",
                )
                if windows_url:
                    windows_model = ask_text("Other computer model name", windows_model)

        permission = ask_choice(
            "How hands-on should Night Shift be?",
            [
                ("brief", "Read-only: make a morning brief"),
                ("draft-local", "Work locally: make tested changes in disposable copies"),
                ("draft-prs", "Autopilot: make tested changes and open draft PRs for review"),
            ],
            permission if permission in {"brief", "draft-local", "draft-prs"} else DEFAULT_PERMISSION,
        )
        selected_autonomy = autonomy_flags(permission)
        execute_drafts = selected_autonomy["execute_drafts"]
        run_checks = selected_autonomy["run_checks"]
        run_e2e = selected_autonomy["run_e2e"]
        allow_draft_prs = selected_autonomy["allow_draft_prs"]
        mode = ask_choice(
            "How much energy should it use?",
            [
                ("quiet", "Quiet: light work, low heat"),
                ("night-shift", "Normal: good overnight run"),
                ("afterburner", "Afterburner: use more compute and make more artifacts"),
            ],
            mode if mode in MODE_DEFAULTS else "night-shift",
        )
        stop = ask_choice(
            "When should Night Shift stop?",
            [
                ("morning", "When I come back and say stop"),
                ("2h", "After 2 hours"),
                ("6h", "After 6 hours"),
                ("8h", "After 8 hours"),
                ("10h", "After 10 hours"),
            ],
            stop if stop in STOP_SECONDS else "morning",
        )

    config = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "project": {
            "repo": repo_text,
            "privacy": project_private,
        },
        "preferences": {
            "wake_goal": wake_goal,
            "privacy_route": privacy_route,
            "permission": permission,
            "mode": mode,
            "stop": stop,
            "guidance": guidance,
            "goal_text": goal_text,
            "allow_cloud_reasoning": privacy_route == "cloud-ok",
            "allow_remote_lan_worker": privacy_route == "mac-and-lan",
            "scope": scope,
            "active_days": active_days,
            "max_repos": max_repos,
            "priority_repos": priority_repos,
            "quiet_hours": quiet_hours,
            "execute_drafts": execute_drafts,
            "run_e2e": run_e2e,
            "run_checks": run_checks,
            "allow_draft_prs": allow_draft_prs,
        },
        "legacy": {
            "local_url": local_url,
            "local_model": local_model,
            "windows_url": windows_url,
            "windows_model": windows_model,
        },
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if local_url:
        os.environ["MAESTRO_LOCAL_BASE_URL"] = local_url.rstrip("/")
    if local_model:
        os.environ["MAESTRO_LOCAL_MODEL"] = local_model
    if windows_url:
        os.environ["WINDOWS_WORKER_BASE_URL"] = windows_url.rstrip("/")
    if windows_model:
        os.environ["WINDOWS_WORKER_MODEL"] = windows_model

    overall, rows = doctor_checks(repo_text, run_smoke=False, allow_fetch=False)
    if args.dry_run:
        print(start_preview(config, rows))
        print("")
        print("Dry run complete. Nothing was saved or started.")
        print("NIGHTSHIFT_START: GREEN | dry run only | no changes saved")
        return 0

    setup_changed = setup_has_changed(saved, config)
    setup_ledger = None

    def persist_setup() -> None:
        nonlocal setup_ledger
        if not setup_changed:
            return
        save_config(config)
        setup_ledger = create_ledger("setup")
        write_startup_gate(setup_ledger, overall, rows)
        write_lab_files(setup_ledger, config, rows)

    print(start_preview(config, rows))
    print("")

    if args.setup_only:
        persist_setup()
        if setup_changed:
            print(f"Saved setup: {CONFIG_PATH}")
            print(f"Setup lab: {setup_ledger / 'lab'}")
            print("All set. I saved setup and did not start a run.")
            print("NIGHTSHIFT_START: GREEN | setup saved | no run started")
        else:
            print(f"Reusing saved setup unchanged: {CONFIG_PATH}")
            print("All set. Your existing setup is ready; no run was started.")
            print("NIGHTSHIFT_START: GREEN | setup unchanged | no run started")
        return 0

    if not args.yes and is_interactive():
        if not ask_yes_no("Start Night Shift now?", default=True):
            print("Nothing new was saved or started.")
            print("NIGHTSHIFT_START: GREEN | start declined | no changes saved")
            return 0

    persist_setup()
    if setup_changed:
        print(f"Saved setup: {CONFIG_PATH}")
        print(f"Setup lab: {setup_ledger / 'lab'}")
    else:
        print(f"Reusing saved setup unchanged: {CONFIG_PATH}")
    if privacy_route == "cloud-ok":
        print("Cloud note: Night Shift will still store credentials outside config and will not send secrets on purpose.")

    by_name = rows_by_name(rows)
    local_ready = (
        by_name.get("local-models", ("", ""))[0] == "GREEN"
        and by_name.get("local-chat", ("", ""))[0] == "GREEN"
    )
    windows_ready = (
        privacy_route == "mac-and-lan"
        and by_name.get("windows-worker", ("", ""))[0] == "GREEN"
    )

    if not local_ready and not windows_ready:
        print("")
        print("I cannot reach worker AI yet, so I will make a simple planning brief instead of pretending to run overnight.")
        print("Next easy fix: open LM Studio and start the local server, or start Ollama, then rerun `night-shift start`.")
        plan_args = argparse.Namespace(repo=repo_text, mode="quiet")
        return command_plan(plan_args)

    run_args = argparse.Namespace(
        repo=repo_text,
        mode=mode,
        permission=permission,
        guidance=guidance,
        goal=goal_text,
        max_local=None,
        max_windows=None,
        parallel_local=None,
        parallel_windows=None,
        token_target=None,
        local_url=local_url,
        local_model=local_model,
        windows_url=windows_url,
        windows_model=windows_model,
        privacy_route=privacy_route,
        wake_goal=wake_goal,
        timeout=args.timeout,
        skip_smoke=args.skip_smoke,
        stop_after=stop,
        scope=scope,
        active_days=active_days,
        max_repos=max_repos,
        task_limit=None,
        poll_minutes=None,
        execute_drafts=execute_drafts,
        run_e2e=run_e2e,
        run_checks=run_checks,
        allow_draft_prs=allow_draft_prs,
        once=getattr(args, "once", False),
        unattended=False,
    )
    return command_autopilot(run_args)

