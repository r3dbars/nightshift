"""Night Shift command handlers. Names resolve from night_shift_cli at call time."""
from __future__ import annotations

from night_shift_commands._bind import bind_cli


@bind_cli
def command_plan(args) -> int:
    ledger = create_ledger(args.mode)
    root = require_git_repo(args.repo)
    if not root:
        return 1
    context = repo_context_pack(root if root and root.exists() else None)
    scan = repo_signal_scan(root)
    write_repo_scan(ledger, scan)
    queue = build_repo_work_queue(root, scan, args.mode, "brief")
    (ledger / "board.md").write_text(build_board(args.mode, queue, "brief"), encoding="utf-8")
    safe_queue = [sanitize_task_for_ledger(item) for item in queue]
    (ledger / "planned-work-queue.json").write_text(json.dumps(safe_queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ledger / "context-pack.txt").write_text(context, encoding="utf-8")
    (ledger / "mode.json").write_text(json.dumps({"mode": args.mode, **MODE_DEFAULTS[args.mode]}, indent=2) + "\n", encoding="utf-8")
    (ledger / "startup-gate.md").write_text("# Startup Gate\n\nStatus: NOT_RUN\n\nRun `night-shift doctor --repo <repo>` before a real night.\n", encoding="utf-8")
    (ledger / "token-report.txt").write_text(
        "No model calls ran. Worker AI was unavailable or this was an explicit planning pass.\n",
        encoding="utf-8",
    )
    planned = []
    for index, item in enumerate(safe_queue[:3], 1):
        raw = str(item.get("prompt") or item.get("reason") or item.get("slug") or "Repo task")
        planned.append(f"{index}. {' '.join(redact(raw).split())[:180]}")
    if not planned:
        planned = ["1. No grounded task was ready yet. Try again after the repo changes."]
    morning = [
        "# Morning Brief", "", "Status: YELLOW", "",
        "Good morning - Night Shift completed a planning-only pass.", "",
        "Start here:",
        "- Start your local model server, then run `night-shift start` again to unlock tested patches.", "",
        "Useful work found:", *planned, "",
        "Run totals:",
        "- Model calls: 0",
        "- Draft PRs opened: 0",
        "- Verified local patches: 0",
        "- Nothing merged, released, or deployed", "",
        "Proof files:",
        f"- Repo scan: {ledger / 'repo-scan.md'}",
        f"- Planned queue: {ledger / 'planned-work-queue.json'}",
        f"- Startup gate: {ledger / 'startup-gate.md'}",
    ]
    (ledger / "morning.md").write_text("\n".join(morning) + "\n", encoding="utf-8")
    print(f"NIGHTSHIFT_PLAN: GREEN | mode={args.mode} | ledger={ledger}")
    print(f"Next: night-shift run --repo {root} --mode {args.mode}")
    print(f"Preview: night-shift report --ledger {ledger}")
    return 0

@bind_cli
def command_run(args) -> int:
    privacy_route = resolve_run_privacy(args)
    apply_compute_overrides(args)
    if not validate_run_args(args):
        return 2
    no_local = bool(getattr(args, "no_local", False))
    no_windows = bool(getattr(args, "no_windows", False))
    defaults = MODE_DEFAULTS[args.mode].copy()
    max_local = defaults["local"] if args.max_local is None else args.max_local
    max_windows = defaults["windows"] if args.max_windows is None else args.max_windows
    max_local, max_windows = apply_privacy_lane_limits(
        max_local, max_windows, privacy_route
    )
    if no_local:
        max_local = 0
    if no_windows:
        max_windows = 0
    parallel_local = defaults["parallel_local"] if args.parallel_local is None else args.parallel_local
    parallel_windows = defaults["parallel_windows"] if args.parallel_windows is None else args.parallel_windows
    target_tokens = defaults["target_tokens"] if args.token_target is None else args.token_target
    stop_after = getattr(args, "stop_after", None)
    permission = getattr(args, "permission", "brief") or "brief"
    guidance = getattr(args, "guidance", "scan") or "scan"
    goal_text = getattr(args, "goal", "") or ""
    deadline = getattr(args, "deadline", None) or stop_deadline(stop_after)

    ledger = create_ledger(args.mode)
    setattr(args, "result_ledger", str(ledger))
    if getattr(args, "unattended", False):
        (ledger / "UNATTENDED").write_text("scheduled nightly run\n", encoding="utf-8")
    root = require_git_repo(args.repo)
    if not root:
        finalize_empty_run(
            ledger,
            args.mode,
            defaults["target_tokens"] if args.token_target is None else args.token_target,
            "RED",
        )
        print(f"NIGHTSHIFT_RUN: RED | invalid repo | ledger={ledger}")
        return 1
    (ledger / "mode.json").write_text(
        json.dumps(
            {
                "mode": args.mode,
                "repo": str(root) if root else args.repo,
                "max_local": max_local,
                "max_windows": max_windows,
                "parallel_local": parallel_local,
                "parallel_windows": parallel_windows,
                "token_target": target_tokens,
                "stop_after": stop_after or "morning",
                "permission": permission,
                "guidance": guidance,
                "goal": goal_text,
                "task_limit": getattr(args, "task_limit", None),
                "privacy_route": privacy_route,
                "run_e2e": bool(getattr(args, "run_e2e", False)),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    overall, rows = doctor_checks(
        args.repo,
        run_smoke=not args.skip_smoke,
        allow_fetch=False,
        skip_local=no_local,
        skip_windows=no_windows,
    )
    write_startup_gate(ledger, overall, rows)
    write_lab_files(
        ledger,
        {
            "project": {"repo": str(root)},
            "preferences": {
                "wake_goal": getattr(args, "wake_goal", "brief"),
                "privacy_route": getattr(args, "privacy_route", "mac-only"),
                "mode": args.mode,
                "stop": stop_after or "morning",
                "permission": permission,
                "guidance": guidance,
                "goal_text": goal_text,
            },
            "legacy": {
                "local_url": "" if no_local else getattr(args, "local_url", None) or os.environ.get("MAESTRO_LOCAL_BASE_URL", DEFAULT_LOCAL_URL),
                "local_model": "" if no_local else getattr(args, "local_model", None) or os.environ.get("MAESTRO_LOCAL_MODEL", DEFAULT_LOCAL_MODEL),
                "windows_url": "" if no_windows else getattr(args, "windows_url", None) or os.environ.get("WINDOWS_WORKER_BASE_URL", ""),
                "windows_model": "" if no_windows else getattr(args, "windows_model", None) or os.environ.get("WINDOWS_WORKER_MODEL", DEFAULT_WINDOWS_MODEL),
            },
        },
        rows,
    )
    context = repo_context_pack(root if root and root.exists() else None)
    scan = repo_signal_scan(root)
    if getattr(args, "run_checks", False):
        check_proof = run_approved_check(root, scan, ledger)
        check_proof["proof"] = str(ledger / "verification-proof.json")
        scan["verification_result"] = check_proof
    if getattr(args, "run_e2e", False):
        e2e_proof = run_approved_e2e(root, scan, ledger)
        e2e_proof["proof"] = str(ledger / "e2e-proof.json")
        scan["e2e_result"] = e2e_proof
    write_repo_scan(ledger, scan)
    discovered_queue = pin_queue_revision(
        build_repo_work_queue(root, scan, args.mode, permission, guidance, goal_text),
        str(scan.get("head") or ""),
    )
    queue, readiness_skips = model_ready_tasks(
        discovered_queue, args.mode, getattr(args, "goal", ""), permission
    )
    queue, feedback_skips = apply_task_feedback(queue, load_feedback(), str(root), args.mode)
    grounded_queue_count = len(queue)
    discovered_queue_count = len(discovered_queue)
    repo_name = scan.get("github_slug") or str(root)
    history = load_task_history()
    attempts = latest_attempts(TASK_ATTEMPTS_PATH)
    for item in queue:
        item["task_revision"] = task_revision_for(root, item, str(scan.get("head") or ""))
        item["fingerprint"] = task_fingerprint(repo_name, item["task_revision"], item)
    queue, review_skips = apply_review_outcomes(
        queue, load_review_outcomes(), str(root), str(scan.get("head") or "")
    )
    skipped: list[dict] = [*readiness_skips, *feedback_skips, *review_skips]
    eligible = []
    for item in queue:
        allowed, reason = may_attempt(
            attempts.get(item["fingerprint"]), item["fingerprint"], item["task_revision"]
        )
        if item["fingerprint"] in history:
            skipped.append({
                "fingerprint": item["fingerprint"],
                "category": "repeat",
                "reason": "already accepted for unchanged task files",
            })
        elif allowed:
            eligible.append(item)
        else:
            skipped.append({"fingerprint": item["fingerprint"], "category": "cooldown", "reason": reason})
    queue = eligible
    rejection_budget = REJECTION_BUDGET[args.mode]
    prior_rejections = rejection_count(TASK_ATTEMPTS_PATH, repo_name, scan.get("head", ""))
    circuit_bypass_tasks = fresh_explicit_goal_tasks(queue, attempts, guidance, goal_text)
    recurring_audit_tasks = [item for item in queue if item.get("recurrence") in {"daily", "weekly"}]
    circuit_bypassed = prior_rejections >= rejection_budget and bool(
        circuit_bypass_tasks or recurring_audit_tasks
    )
    if prior_rejections >= rejection_budget:
        # The circuit blocks stale coding ideas, but recurring report-only audits
        # are deliberately fresh and bounded work for an otherwise quiet repo.
        queue = []
        seen_slugs: set[str] = set()
        for item in [*circuit_bypass_tasks, *recurring_audit_tasks]:
            slug = str(item.get("slug") or "")
            if slug and slug not in seen_slugs:
                seen_slugs.add(slug)
                queue.append(item)
        circuit_status = (
            "BYPASSED_FOR_NEW_EXPLICIT_GOAL" if circuit_bypass_tasks
            else "BYPASSED_FOR_RECURRING_AUDITS" if recurring_audit_tasks
            else "OPEN"
        )
        (ledger / "model-circuit.json").write_text(
            json.dumps(
                {
                    "status": circuit_status,
                    "repo": repo_name,
                    "head": scan.get("head", ""),
                    "rejections": prior_rejections,
                    "budget": rejection_budget,
                    "fresh_goal_tasks": len(circuit_bypass_tasks),
                    "fresh_goal_bypass": circuit_bypassed,
                },
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    lifecycle_path = ledger / "task-lifecycle.jsonl"
    for item in queue:
        record_state(
            lifecycle_path, item["fingerprint"], "DISCOVERED",
            repo=repo_name, head=scan.get("head", ""), task=item.get("slug", ""), reason="grounded task queued",
        )
    (ledger / "task-skips.json").write_text(json.dumps(skipped, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    task_limit = getattr(args, "task_limit", None)
    if task_limit is not None:
        queue = queue[: max(0, task_limit)]
    safe_queue = [sanitize_task_for_ledger(item) for item in queue]
    (ledger / "planned-work-queue.json").write_text(json.dumps(safe_queue, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ledger / "context-pack.txt").write_text(context, encoding="utf-8")
    (ledger / "board.md").write_text(build_board(args.mode, queue, permission), encoding="utf-8")

    if any(name in {"local-models", "local-chat"} and state != "GREEN" for name, state, _ in rows):
        max_local = 0
    if any(name == "windows-worker" and state == "YELLOW" for name, state, _ in rows):
        max_windows = 0
    if overall == "RED":
        finalize_empty_run(ledger, args.mode, target_tokens, overall, skipped, scan)
        print(f"NIGHTSHIFT_RUN: RED | startup gate failed | ledger={ledger}")
        return 1
    if max_local == 0 and max_windows == 0:
        finalize_empty_run(ledger, args.mode, target_tokens, overall, skipped, scan)
        print(f"NIGHTSHIFT_RUN: YELLOW | no cheap compute lanes reachable | ledger={ledger}")
        return 0

    tasks = []
    if not queue:
        if grounded_queue_count:
            finalize_empty_run(ledger, args.mode, target_tokens, "GREEN", skipped, scan)
            print(f"NIGHTSHIFT_RUN: YELLOW | no new grounded repo tasks | ledger={ledger}")
            print("Everything at this repo revision was already attempted. Night Shift will wait for new GitHub or code activity.")
            return 0
        if discovered_queue_count:
            finalize_empty_run(ledger, args.mode, target_tokens, "GREEN", skipped, scan)
            print(f"NIGHTSHIFT_RUN: YELLOW | no model-ready tasks; weak signals skipped before dispatch | ledger={ledger}")
            print("Night Shift found repo activity, but none had enough evidence and verification to spend model tokens safely.")
            return 0
        finalize_empty_run(ledger, args.mode, target_tokens, "YELLOW", skipped, scan)
        print(f"NIGHTSHIFT_RUN: YELLOW | no grounded repo tasks found | ledger={ledger}")
        print("Add recent code, tests, issues, or a concrete goal before widening the run.")
        return 0
    local_evidence_packs = {
        item["slug"]: task_evidence_pack(root, item, context, max_chars=7000, max_files=2) for item in queue
    }
    windows_evidence_packs = {
        item["slug"]: task_evidence_pack(root, item, context, max_chars=12000, max_files=3) for item in queue
    }
    lane_counts = {"local": 0, "windows": 0}
    lane_caps = {"local": max_local, "windows": max_windows}
    for item in queue:
        lane = item.get("preferred_lane", "local")
        fallback = "windows" if lane == "local" else "local"
        if lane_caps[lane] <= lane_counts[lane]:
            lane = fallback
        if lane_caps[lane] <= lane_counts[lane]:
            continue
        slug, text = item["slug"], item["prompt"]
        candidate_files = item.get("files", [])[:9]
        prompt = (
            local_prompt(slug, text, local_evidence_packs[slug], item, permission)
            if lane == "local"
            else windows_prompt(slug, text, windows_evidence_packs[slug], item, permission)
        )
        tasks.append(
            (
                lane,
                slug,
                prompt,
                candidate_files,
                item.get("verification_commands", []),
                item["fingerprint"],
                item["task_revision"],
                item.get("ladder", "strengthen"),
                item.get("proof_kind", "source"),
                bool(item.get("executable", False)),
                item.get("evidence_sources", {}),
                item.get("source_ref", ""),
                item.get("kind") == "issue",
                item.get("kind", ""),
                item.get("semantic_contract", {}),
                item.get("draft_intent", ""),
            )
        )
        lane_counts[lane] += 1

    results: list[dict] = []
    stop_file = ledger / "STOP"
    total_workers = max(1, parallel_local + parallel_windows)
    lane_limits = {"local": max(1, parallel_local), "windows": max(1, parallel_windows)}
    lane_running = {"local": 0, "windows": 0}
    circuit = {
        "rejections": prior_rejections,
        "budget": rejection_budget,
        "opened": prior_rejections >= rejection_budget and not circuit_bypassed,
    }

    def submit_ready(executor, pending, remaining):
        submitted = 0
        for item in list(remaining):
            if circuit["opened"]:
                break
            (
                lane,
                label,
                prompt,
                candidate_files,
                verification_commands,
                fingerprint,
                task_revision,
                ladder,
                proof_kind,
                executable,
                evidence_sources,
                source_ref,
                pinned_issue,
                kind,
                semantic_contract,
                draft_intent,
            ) = item
            if lane_running[lane] >= lane_limits[lane]:
                continue
            if stop_file.exists():
                break
            if deadline_reached(deadline, stop_file):
                break
            lane_running[lane] += 1
            future = executor.submit(
                dispatch_one,
                lane,
                label,
                prompt,
                ledger,
                args.mode,
                args.timeout,
                candidate_files,
                verification_commands,
                root,
                proof_kind,
                evidence_sources,
                source_ref,
                pinned_issue,
            )
            pending[future] = {
                "lane": lane,
                "fingerprint": fingerprint,
                "task_revision": task_revision,
                "ladder": ladder,
                "proof_kind": proof_kind,
                "executable": executable,
                "source_ref": source_ref,
                "kind": kind,
                "verification_commands": verification_commands,
                "evidence_sources": evidence_sources,
                "semantic_contract": semantic_contract,
                "draft_intent": draft_intent,
            }
            remaining.remove(item)
            submitted += 1
        return submitted

    remaining = list(tasks)
    pending = {}
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=total_workers)
    hard_stopped = False
    try:
        submit_ready(executor, pending, remaining)
        while pending:
            timeout = 60
            if deadline:
                timeout = max(1, min(60, int(deadline - time.time())))
            done, _ = concurrent.futures.wait(pending, timeout=timeout, return_when=concurrent.futures.FIRST_COMPLETED)
            if not done and deadline_reached(deadline, stop_file):
                cancel_pending_workers(ledger, pending)
                hard_stopped = True
                break
            for future in done:
                pending_item = pending.pop(future)
                lane = pending_item["lane"]
                lane_running[lane] -= 1
                try:
                    result = future.result()
                    result["repo"] = str(root)
                    result["repo_name"] = repo_name
                    result["fingerprint"] = pending_item["fingerprint"]
                    result["task_revision"] = pending_item["task_revision"]
                    result["ladder"] = pending_item["ladder"]
                    result["proof_kind"] = pending_item["proof_kind"]
                    result["executable"] = pending_item["executable"]
                    result["source_ref"] = pending_item["source_ref"]
                    result["kind"] = pending_item["kind"]
                    result["verification_commands"] = pending_item["verification_commands"]
                    result["evidence_sources"] = sanitize_evidence_sources(pending_item["evidence_sources"])
                    result["semantic_contract"] = pending_item["semantic_contract"]
                    result["draft_intent"] = pending_item["draft_intent"]
                    results.append(result)
                    if result.get("score") == "REJECT":
                        circuit["rejections"] += 1
                except Exception as exc:
                    results.append(
                        {
                            "lane": lane,
                            "label": "unknown",
                            "rc": 1,
                            "timed_out": False,
                            "seconds": 0,
                            "proof": "",
                            "artifact": "",
                            "score": "REJECT",
                            "priority": 0,
                            "tokens": 0,
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "summary": str(exc),
                            "output": "",
                            "output_preview": str(exc),
                            "repo": str(root),
                            "repo_name": repo_name,
                            "fingerprint": pending_item["fingerprint"],
                            "task_revision": pending_item["task_revision"],
                            "ladder": pending_item["ladder"],
                            "proof_kind": pending_item["proof_kind"],
                            "executable": pending_item["executable"],
                            "source_ref": pending_item["source_ref"],
                            "kind": pending_item["kind"],
                            "verification_commands": pending_item["verification_commands"],
                            "evidence_sources": sanitize_evidence_sources(pending_item["evidence_sources"]),
                            "semantic_contract": pending_item["semantic_contract"],
                            "draft_intent": pending_item["draft_intent"],
                        }
                    )
                    circuit["rejections"] += 1
                if circuit["rejections"] >= circuit["budget"]:
                    circuit["opened"] = True
                    remaining.clear()
                    (ledger / "model-circuit.json").write_text(
                        json.dumps(
                            {
                                "status": "OPEN",
                                "repo": repo_name,
                                "head": scan.get("head", ""),
                                "rejections": circuit["rejections"],
                                "budget": circuit["budget"],
                                "fresh_goal_bypass": circuit_bypassed,
                            },
                            indent=2,
                        ) + "\n",
                        encoding="utf-8",
                    )
            if stop_file.exists():
                cancel_pending_workers(ledger, pending)
                hard_stopped = True
                break
            submit_ready(executor, pending, remaining)
    finally:
        executor.shutdown(wait=not hard_stopped, cancel_futures=hard_stopped)

    now_epoch = time.time()
    for row in results:
        fingerprint = row.get("fingerprint")
        if not fingerprint:
            continue
        previous = attempts.get(fingerprint, {})
        rejected = row.get("score", "REJECT") == "REJECT"
        append_attempt(
            TASK_ATTEMPTS_PATH,
            {
                "fingerprint": fingerprint,
                "repo": row.get("repo_name", repo_name),
                "head": scan.get("head", ""),
                "task_revision": row.get("task_revision", scan.get("head", "")),
                "state": "REJECTED" if rejected else "DISCOVERED",
                "score": row.get("score", "REJECT"),
                "reason": row.get("summary", "")[:500],
                "epoch": now_epoch,
                "rejections": int(previous.get("rejections", 0)) + 1 if rejected else 0,
            },
        )
        if rejected:
            record_state(
                lifecycle_path, fingerprint, "REJECTED",
                repo=row.get("repo_name", repo_name), head=scan.get("head", ""), reason=row.get("summary", "")[:500],
            )
    append_task_history(
        [
            {
                "fingerprint": row["fingerprint"],
                "repo": row.get("repo_name", repo_name),
                "head": scan.get("head", ""),
                "task_revision": row.get("task_revision", scan.get("head", "")),
                "task": row.get("label", ""),
                "ladder": row.get("ladder", ""),
                "score": row.get("score", "REJECT"),
                "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            for row in results
            if row.get("fingerprint") and row.get("rc") == 0 and row.get("score") in {"KEEP", "MAYBE"}
        ]
    )
    write_harvest(ledger, results)
    write_work_queue(ledger, results)
    write_outcome_metrics(ledger, results, skipped)
    write_task_lifecycle_summary(ledger)
    token_report = write_token_report(ledger, results)
    write_morning(ledger, args.mode, results, target_tokens, overall, scan)
    total_tokens = sum(r["tokens"] for r in results)
    status = run_status(results, target_tokens, overall, args.mode)
    print(
        f"NIGHTSHIFT_RUN: {status} | mode={args.mode} | local={len([r for r in results if r['lane']=='local'])} "
        f"| windows={len([r for r in results if r['lane']=='windows'])} | tokens={total_tokens} | ledger={ledger}"
    )
    print(f"Morning brief: night-shift report --ledger {ledger}")
    print(f"Stop this run: night-shift stop --ledger {ledger}")
    print(token_report.strip())
    return 0

@bind_cli
def command_autopilot(args) -> int:
    saved = load_config()
    args.no_local = bool(getattr(args, "no_local", False))
    args.no_windows = bool(getattr(args, "no_windows", False))
    if args.no_local:
        args.local_url = ""
        args.local_model = ""
    if args.no_windows:
        args.windows_url = ""
        args.windows_model = ""
    if getattr(args, "execute_drafts", None) is None:
        args.execute_drafts = bool(config_value(saved, "execute_drafts", False))
    if getattr(args, "run_e2e", None) is None:
        args.run_e2e = bool(config_value(saved, "run_e2e", False))
    if getattr(args, "run_checks", None) is None:
        args.run_checks = bool(config_value(saved, "run_checks", False))
    args.mode = getattr(args, "mode", None) or config_value(saved, "mode", "night-shift")
    args.scope = getattr(args, "scope", None) or config_value(saved, "scope", "github-recent")
    args.permission = getattr(args, "permission", None) or config_value(saved, "permission", "brief")
    args.guidance = getattr(args, "guidance", None) or config_value(saved, "guidance", "scan")
    args.stop_after = getattr(args, "stop_after", None) or config_value(saved, "stop", "8h")
    if not getattr(args, "repo", None):
        args.repo = config_value(saved, "repo")
    resolve_autopilot_privacy(args, saved)
    resolve_autopilot_wake_goal(args, saved)
    privacy_route = enforce_autopilot_privacy(args)
    if not getattr(args, "allow_draft_prs", False):
        args.allow_draft_prs = bool(config_value(saved, "allow_draft_prs", False))
    for name in ("local_url", "local_model", "windows_url", "windows_model"):
        if name.startswith("local_") and args.no_local:
            continue
        if name == "windows_url" and privacy_route and privacy_route != "mac-and-lan":
            continue
        if name.startswith("windows_") and args.no_windows:
            continue
        if not getattr(args, name, None):
            setattr(args, name, config_value(saved, name))
    requested_active_days = getattr(args, "active_days", None)
    requested_max_repos = getattr(args, "max_repos", None)
    if (
        requested_active_days is not None and requested_active_days < 1
    ) or (
        requested_max_repos is not None and requested_max_repos < 1
    ):
        print("NIGHTSHIFT_AUTOPILOT: RED | --active-days and --max-repos must be positive")
        return 2
    apply_compute_overrides(args)
    mode = args.mode
    defaults = AUTOPILOT_DEFAULTS[mode]
    primary = require_git_repo(args.repo) if getattr(args, "repo", None) else None
    if getattr(args, "repo", None) and not primary:
        return 1
    scope = args.scope
    max_repos = getattr(args, "max_repos", None) or config_value(saved, "max_repos", defaults["repo_limit"])
    priority_repos = PortfolioEngine.normalize_priority_repos(config_value(saved, "priority_repos", []))
    active_days = getattr(args, "active_days", None) or config_value(saved, "active_days", 14)
    if active_days < 1 or max_repos < 1:
        print("NIGHTSHIFT_AUTOPILOT: RED | saved active-days and max-repos must be positive")
        return 2
    task_limit = getattr(args, "task_limit", None) or defaults["task_limit"]
    poll_minutes = getattr(args, "poll_minutes", None) or defaults["poll_minutes"]
    stop_after = args.stop_after
    deadline = stop_deadline(stop_after)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Only one unattended controller is allowed to schedule work at a time.
    lock_context = exclusive_lock(AUTOPILOT_LOCK_PATH)
    acquired = lock_context.__enter__()
    if not acquired:
        args.concurrent_active = _active_autopilot(AUTOPILOT_STATE_PATH) or {"status": "lock-held"}
        lock_context.__exit__(None, None, None)
        print("NIGHTSHIFT_AUTOPILOT: YELLOW | another Night Shift controller is already running")
        return 1
    recovery = recover_stale_autopilot(AUTOPILOT_STATE_PATH, OVERNIGHT_ROOT)
    if recovery.get("status") == "active":
        lock_context.__exit__(None, None, None)
        print("NIGHTSHIFT_AUTOPILOT: YELLOW | active controller state still belongs to a running process")
        return 1
    if recovery.get("status") == "unsafe":
        lock_context.__exit__(None, None, None)
        print(f"NIGHTSHIFT_AUTOPILOT: RED | cannot safely recover prior controller: {recovery.get('reason')}")
        return 1
    if recovery.get("status") == "recovered":
        print(f"Recovered prior crashed shift: {recovery.get('ledger')}")
    started_epoch = time.time()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stop_reason = "unknown"
    try:
        ledger = create_ledger("autopilot")
        setattr(args, "result_ledger", str(ledger))
        if getattr(args, "unattended", False):
            (ledger / "UNATTENDED").write_text("scheduled portfolio run\n", encoding="utf-8")
        stop_file = ledger / "STOP"
        (ledger / "mode.json").write_text(
            json.dumps(
                {
                    "mode": mode,
                    "scope": scope,
                    "repo": str(primary) if primary else "",
                    "max_repos": max_repos,
                    "priority_repos": priority_repos,
                    "active_days": active_days,
                    "task_limit": task_limit,
                    "poll_minutes": poll_minutes,
                    "stop_after": stop_after or "morning",
                    "permission": getattr(args, "permission", "brief"),
                    "run_checks": bool(getattr(args, "run_checks", False)),
                    "run_e2e": bool(getattr(args, "run_e2e", False)),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        lock_context.__exit__(*sys.exc_info())
        raise
    try:
        AUTOPILOT_STATE_PATH.write_text(
            json.dumps({"pid": os.getpid(), "ledger": str(ledger), "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}, indent=2)
            + "\n", encoding="utf-8")
        controller = AutopilotCycleState(ledger)
    except Exception:
        lock_context.__exit__(*sys.exc_info())
        raise
    prepared_cache: list[tuple[dict, Path]] | None = None
    portfolio_cache: list[dict] = []
    next_portfolio_refresh = 0.0

    def stop_cause() -> str:
        if deadline is not None and time.time() >= deadline:
            deadline_reached(deadline, stop_file)
            return "deadline"
        if stop_file.exists():
            return "stop-file"
        return ""

    try:
        while True:
            cause = stop_cause()
            if cause:
                stop_reason = cause
                break
            cycle = controller.start_cycle()
            now = time.time()
            if prepared_cache is None or now >= next_portfolio_refresh:
                if scope == "github-recent":
                    portfolio = discover_github_portfolio(
                        primary,
                        active_days=active_days,
                        max_repos=max_repos,
                        priority_repos=priority_repos,
                    )
                else:
                    portfolio = [
                        {
                            "slug": repo_slug(primary) or (primary.name if primary else "current"),
                            "primary": True,
                            "score": 1000,
                            "signals": github_repo_signals(repo_slug(primary)),
                            "path": str(primary) if primary else "",
                        }
                    ] if primary else []
                prepared = []
                for item in portfolio:
                    checkout, checkout_status = ensure_portfolio_checkout(item, primary)
                    item["checkout_status"] = checkout_status
                    item["checkout"] = str(checkout) if checkout else ""
                    if checkout:
                        if getattr(args, "execute_drafts", False):
                            ready, readiness = ensure_repo_autonomy(
                                checkout, bool(getattr(args, "run_e2e", False))
                            )
                            item["autonomy_ready"] = ready
                            item["autonomy_status"] = readiness
                        prepared.append((item, checkout))
                prepared_cache = prepared
                portfolio_cache = portfolio
                next_portfolio_refresh = now + max(60, poll_minutes * 60)
            else:
                prepared = prepared_cache
                portfolio = portfolio_cache
            write_portfolio_snapshot(ledger, portfolio, cycle)
            if not prepared:
                controller.no_prepared_repositories()
                stop_reason = "no-prepared-repositories"
                break
            per_repo_limit = max(1, task_limit // len(prepared))
            for portfolio_rank, (item, checkout) in enumerate(prepared, start=1):
                cause = stop_cause()
                if cause:
                    stop_reason = cause
                    break
                repo_name = item.get("slug", str(checkout))
                if controller.should_skip_attempted_repo(repo_name):
                    cycle_row = controller.record_attempted_skip(repo=repo_name, checkout=checkout)
                    signals = item.get("signals") or {}
                    cycle_row.update({
                        "portfolio_rank": portfolio_rank,
                        "portfolio_score": int(item.get("score") or 0),
                        "portfolio_primary": bool(item.get("primary")),
                        "portfolio_priority": bool(item.get("priority")),
                        "portfolio_reason": PORTFOLIO.selection_reason(item),
                        "portfolio_signals": {
                            "failed_runs": len(signals.get("failed_runs") or []),
                            "issues": len(signals.get("issues") or []),
                            "prs": len(signals.get("prs") or []),
                            "actionable_prs": int(signals.get("actionable_prs") or 0),
                            "ready_prs": int(signals.get("ready_prs") or 0),
                            "draft_prs": int(signals.get("draft_prs") or 0),
                        },
                    })
                    controller.append(cycle_row)
                    continue
                remaining_seconds = int(deadline - time.time()) if deadline else getattr(args, "timeout", 900)
                if remaining_seconds <= 0:
                    break
                child_args = argparse.Namespace(
                    repo=str(checkout),
                    mode=mode,
                    permission=args.permission,
                    guidance=args.guidance,
                    goal=getattr(args, "goal", ""),
                    max_local=0 if args.no_local else None,
                    max_windows=0 if args.no_windows else None,
                    parallel_local=None,
                    parallel_windows=None,
                    token_target=None,
                    local_url=getattr(args, "local_url", None),
                    local_model=getattr(args, "local_model", None),
                    windows_url=getattr(args, "windows_url", None),
                    windows_model=getattr(args, "windows_model", None),
                    no_local=args.no_local,
                    no_windows=args.no_windows,
                    timeout=max(1, min(getattr(args, "timeout", 900), remaining_seconds)),
                    skip_smoke=getattr(args, "skip_smoke", False),
                    stop_after=getattr(args, "stop_after", None),
                    deadline=deadline,
                    task_limit=per_repo_limit,
                    unattended=False,
                    wake_goal=getattr(args, "wake_goal", "brief"),
                    privacy_route=getattr(args, "privacy_route", "mac-only"),
                    run_e2e=getattr(args, "run_e2e", False),
                    run_checks=getattr(args, "run_checks", False),
                )
                rc = command_run(child_args)
                child_ledger = Path(child_args.result_ledger)
                child_morning = child_ledger / "morning.md"
                planned = parse_json_text((child_ledger / "planned-work-queue.json").read_text(encoding="utf-8"), [])
                cycle_row = controller.record_child(
                    repo=item.get("slug", str(checkout)), checkout=checkout,
                    child_ledger=child_ledger, return_code=rc,
                    child_is_green=morning_status(child_morning) == "GREEN",
                    planned_count=len(planned),
                )
                signals = item.get("signals") or {}
                portfolio_reason = PORTFOLIO.selection_reason(item)
                cycle_row.update({
                    "portfolio_rank": portfolio_rank,
                    "portfolio_score": int(item.get("score") or 0),
                    "portfolio_primary": bool(item.get("primary")),
                    "portfolio_priority": bool(item.get("priority")),
                    "portfolio_reason": portfolio_reason,
                    "portfolio_signals": {
                        "failed_runs": len(signals.get("failed_runs") or []),
                        "issues": len(signals.get("issues") or []),
                        "prs": len(signals.get("prs") or []),
                        "actionable_prs": int(signals.get("actionable_prs") or 0),
                        "ready_prs": int(signals.get("ready_prs") or 0),
                        "draft_prs": int(signals.get("draft_prs") or 0),
                    },
                })
                if controller.may_draft(
                    cycle_row["repo"], getattr(args, "execute_drafts", False),
                    args.permission,
                ):
                    candidate = select_draft_candidate(child_ledger, checkout)
                    draft_timeout = remaining_draft_timeout(
                        getattr(args, "timeout", 900), deadline, stop_file
                    )
                    if candidate and draft_timeout > 0:
                        draft = run_isolated_draft(
                            checkout,
                            cycle_row["repo"],
                            candidate,
                            ledger,
                            draft_timeout,
                            "" if args.no_local else getattr(args, "local_url", "") or os.environ.get("MAESTRO_LOCAL_BASE_URL", ""),
                            "" if args.no_local else getattr(args, "local_model", "") or os.environ.get("MAESTRO_LOCAL_MODEL", ""),
                            "" if args.no_windows else getattr(args, "windows_url", "") or os.environ.get("WINDOWS_WORKER_BASE_URL", ""),
                            "" if args.no_windows else getattr(args, "windows_model", "") or os.environ.get("WINDOWS_WORKER_MODEL", DEFAULT_WINDOWS_MODEL),
                            deadline,
                            stop_file,
                        )
                        controller.finish_draft_attempt(cycle_row, draft)
                        if controller.may_publish_now(
                            cycle_row["repo"],
                            args.permission,
                            getattr(args, "allow_draft_prs", False),
                            str(draft.get("status") or ""),
                        ):
                            profile, _ = load_repo_profile(checkout)
                            proof_path = Path(str(draft.get("proof") or ""))
                            if profile and proof_path.parent.exists():
                                publish_dir = proof_path.parent / f"{proof_path.stem}-publish"
                                publish = publish_engine().publish(
                                    checkout, cycle_row["repo"], draft, profile, publish_dir,
                                    repo_dependency_source(checkout, profile),
                                )
                                controller.attach_publish(cycle_row, publish)
                    else:
                        controller.finish_draft_attempt(cycle_row, None)
                child_metrics = parse_json_text(
                    (child_ledger / "outcome-metrics.json").read_text(encoding="utf-8"), {}
                ) if (child_ledger / "outcome-metrics.json").exists() else {}
                draft_status = str((cycle_row.get("draft") or {}).get("status") or "")
                if draft_status in VERIFIED_DRAFT_STATUSES:
                    child_metrics = record_verified_outcome(child_ledger, draft_status)
                cycle_row["outcomes"] = {
                    "candidate_count": int(child_metrics.get("accepted_candidates") or 0),
                    "candidate_only_candidates": int(child_metrics.get("candidate_only_candidates") or 0),
                    "draft_pr_opened": int(bool((cycle_row.get("publish") or {}).get("pr_url"))),
                    "estimated_tokens": int(child_metrics.get("estimated_tokens") or 0),
                    "hosted_check_count": int(((cycle_row.get("publish") or {}).get("hosted_checks") or {}).get("check_count") or 0),
                    "hosted_checks_state": str(((cycle_row.get("publish") or {}).get("hosted_checks") or {}).get("state") or ""),
                    "tokens_per_verified_draft": float(child_metrics.get("tokens_per_verified_draft") or 0),
                    "verified_drafts": int(child_metrics.get("verified_drafts") or 0),
                    "verified_outcome_tokens": int(child_metrics.get("verified_outcome_tokens") or 0),
                }
                append_repo_outcome(REPO_OUTCOMES_PATH, {
                    "accepted_candidates": int(child_metrics.get("accepted_candidates") or 0),
                    "candidate_only_candidates": int(child_metrics.get("candidate_only_candidates") or 0),
                    "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "draft_pr_opened": int(bool((cycle_row.get("publish") or {}).get("pr_url"))),
                    "estimated_tokens": int(child_metrics.get("estimated_tokens") or 0),
                    "hosted_check_count": int(((cycle_row.get("publish") or {}).get("hosted_checks") or {}).get("check_count") or 0),
                    "hosted_checks_state": str(((cycle_row.get("publish") or {}).get("hosted_checks") or {}).get("state") or ""),
                    "repo": cycle_row["repo"],
                    "source_ref": str((planned[0].get("source_ref") if planned else "") or ""),
                    "tokens_per_verified_draft": float(child_metrics.get("tokens_per_verified_draft") or 0),
                    "verified_drafts": int(child_metrics.get("verified_drafts") or 0),
                    "verified_outcome_tokens": int(child_metrics.get("verified_outcome_tokens") or 0),
                })
                controller.append(cycle_row)
            portfolio_brief(ledger, controller.rows, controller.status)
            if getattr(args, "once", False):
                stop_reason = "once"
                break
            if not controller.cycle_had_work:
                sleep_for = poll_minutes * 60
                if deadline:
                    sleep_for = min(sleep_for, max(0, int(deadline - time.time())))
                for _ in range(max(0, sleep_for)):
                    if stop_file.exists():
                        stop_reason = "stop-file"
                        break
                    time.sleep(1)
            cause = stop_cause()
            if cause:
                stop_reason = cause
                break
        portfolio_brief(ledger, controller.rows, controller.status)
    except Exception:
        stop_reason = "error"
        raise
    finally:
        if stop_reason == "unknown":
            stop_reason = "stop-file" if stop_file.exists() else "completed"
        write_autopilot_summary(
            ledger,
            controller,
            started_at=started_at,
            started_epoch=started_epoch,
            stop_after=stop_after,
            stop_reason=stop_reason,
        )
        portfolio_brief(ledger, controller.rows, controller.status)
        try:
            active = parse_json_text(AUTOPILOT_STATE_PATH.read_text(encoding="utf-8"), {})
            if active.get("pid") == os.getpid():
                AUTOPILOT_STATE_PATH.unlink(missing_ok=True)
        except OSError:
            pass
        lock_context.__exit__(None, None, None)
    print(f"NIGHTSHIFT_AUTOPILOT: {controller.status} | cycles={controller.cycle} | stop={stop_reason} | ledger={ledger}")
    print(f"Morning brief: night-shift report --ledger {ledger}")
    action_required = controller.action_required()
    return 0 if controller.status == "GREEN" or not action_required else 1

@bind_cli
def command_nightly(args) -> int:
    config = load_config()
    repo = config_value(config, "repo")
    if not repo:
        write_last_nightly("RED", "no saved setup; run night-shift start")
        print("NIGHTSHIFT_NIGHTLY: RED | no saved setup | run `night-shift start` once")
        return 2
    snoozed = snooze_until()
    if snoozed:
        write_last_nightly("SKIPPED", f"snoozed until {snoozed}")
        print(f"NIGHTSHIFT_NIGHTLY: GREEN | skipped | snoozed until {snoozed}")
        return 0
    quiet_hours = normalize_quiet_hours(config_value(config, "quiet_hours", ""))
    if quiet_hours_active(quiet_hours):
        write_last_nightly("SKIPPED_QUIET_HOURS", f"quiet hours {quiet_hours}")
        print(f"NIGHTSHIFT_NIGHTLY: GREEN | skipped | quiet hours {quiet_hours}")
        return 0
    pending = unreviewed_briefs()
    if len(pending) >= UNREVIEWED_CAP:
        write_last_nightly("PAUSED", f"{len(pending)} unreviewed briefs")
        print(f"NIGHTSHIFT_NIGHTLY: YELLOW | paused | {len(pending)} overnight briefs are waiting unread")
        print("Night Shift stops making new briefs nobody reads. Catch up with:")
        print("  night-shift report --latest")
        return 0
    active = _active_autopilot(AUTOPILOT_STATE_PATH)
    if active:
        ledger = Path(str(active.get("ledger") or ""))
        detail = f"shift already running pid={active.get('pid')}"
        write_last_nightly("SKIPPED_ACTIVE", detail, ledger if ledger.exists() else None)
        print(f"NIGHTSHIFT_NIGHTLY: GREEN | skipped | {detail}")
        return 0
    mode = config_value(config, "mode", "night-shift")
    power_state, _ = check_power()
    if power_state == "YELLOW" and mode != "quiet":
        mode = "quiet"
    run_args = argparse.Namespace(
        repo=repo,
        mode=mode,
        permission=config_value(config, "permission", "brief"),
        guidance=config_value(config, "guidance", "scan"),
        goal=config_value(config, "goal_text", ""),
        max_local=None,
        max_windows=None,
        parallel_local=None,
        parallel_windows=None,
        token_target=None,
        local_url=config_value(config, "local_url"),
        local_model=config_value(config, "local_model"),
        windows_url=config_value(config, "windows_url") if config_value(config, "privacy_route") == "mac-and-lan" else None,
        windows_model=config_value(config, "windows_model"),
        privacy_route=config_value(config, "privacy_route", "mac-only"),
        timeout=900,
        skip_smoke=False,
        stop_after=config_value(config, "stop", "8h") if config_value(config, "stop") != "morning" else "8h",
        unattended=True,
        scope=configured_scope(config),
        active_days=config_value(config, "active_days", 14),
        max_repos=config_value(config, "max_repos", AUTOPILOT_DEFAULTS[mode]["repo_limit"]),
        task_limit=None,
        poll_minutes=None,
        execute_drafts=config_value(config, "execute_drafts", False),
        run_e2e=config_value(config, "run_e2e", False),
        run_checks=config_value(config, "run_checks", False),
        once=getattr(args, "once", False),
    )
    rc = command_autopilot(run_args)
    concurrent = getattr(run_args, "concurrent_active", None)
    if concurrent:
        ledger = Path(str(concurrent.get("ledger") or ""))
        write_last_nightly(
            "SKIPPED_ACTIVE", "another shift won the scheduler race",
            ledger if ledger.exists() else None,
        )
        print("NIGHTSHIFT_NIGHTLY: GREEN | skipped | another shift won the scheduler race")
        return 0
    ledgers = unattended_ledgers()
    newest = ledgers[-1] if ledgers else None
    write_last_nightly("GREEN" if rc == 0 else "YELLOW", f"run exit {rc}", newest)
    if rc == 0 and config_value(config, "deliver") == "github-issue" and newest:
        deliver_args = argparse.Namespace(latest=False, ledger=str(newest), github_issue=True)
        command_deliver(deliver_args)
    return rc

