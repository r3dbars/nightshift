"""Night Shift command handlers. Names resolve from night_shift_cli at call time."""
from __future__ import annotations

from night_shift_commands._bind import bind_cli


@bind_cli
def command_clean(args) -> int:
    if args.days < 1:
        print("NIGHTSHIFT_CLEAN: RED | --days must be at least 1")
        return 2
    candidates = cleanup_candidates(OVERNIGHT_ROOT, args.days)
    total = sum(directory_size(path) for path in candidates)
    if not args.apply:
        print(f"NIGHTSHIFT_CLEAN: GREEN | would reclaim {round(total / 1024**2, 1)} MB from {len(candidates)} reviewed ledger(s) older than {args.days} days")
        print("Nothing was removed. Run `night-shift clean --apply` when this list looks right.")
        for path in candidates[:10]:
            print(f"- {path}")
        return 0
    removed = 0
    for path in candidates:
        shutil.rmtree(path)
        removed += 1
    print(f"NIGHTSHIFT_CLEAN: GREEN | reclaimed {round(total / 1024**2, 1)} MB from {removed} reviewed ledger(s)")
    return 0

@bind_cli
def command_reconcile_drafts(args) -> int:
    """Refresh local hosted-check evidence for already opened draft PRs."""
    repo = require_git_repo(args.repo)
    if not repo:
        return 1
    rows = publish_engine().reconcile_drafts(repo)
    drafts = [row for row in rows if row.get("status") == "DRAFT_PR_OPENED" and row.get("pr_url")]
    if not drafts:
        print("NIGHTSHIFT_DRAFT_STATUS: GREEN | no recorded draft PRs to reconcile")
        return 0
    print(f"NIGHTSHIFT_DRAFT_STATUS: GREEN | reconciled={len(drafts)} | local ledger only")
    for row in drafts:
        hosted = row.get("hosted_checks") or {}
        print(
            f"- {row['pr_url']} | draft={row.get('draft_state', 'unknown')} "
            f"checks={hosted.get('state', 'unknown')} count={hosted.get('check_count', 0)}"
        )
    return 0

@bind_cli
def command_schedule(args) -> int:
    config = load_config()
    if args.off:
        state, message = remove_schedule()
        config.pop("schedule", None)
        save_config(config)
        print(f"NIGHTSHIFT_SCHEDULE: {state} | {message}")
        return 0
    if args.nightly:
        parsed = parse_nightly_time(args.nightly)
        if not parsed:
            print("NIGHTSHIFT_SCHEDULE: RED | use --nightly HH:MM, for example --nightly 23:30")
            return 2
        if not config:
            print("NIGHTSHIFT_SCHEDULE: RED | run `night-shift start` once first so the nightly run has saved answers")
            return 2
        hour, minute = parsed
        state, message = install_schedule(hour, minute)
        config["schedule"] = {"time": f"{hour:02d}:{minute:02d}", "method": schedule_installed() or "manual"}
        save_config(config)
        print(f"NIGHTSHIFT_SCHEDULE: {state} | nightly at {hour:02d}:{minute:02d} | {message}")
        print(f"It runs: {nightly_command_line()}")
        print("Check anytime: night-shift schedule --status")
        print("Turn off anytime: night-shift schedule --off")
        return 0 if state == "GREEN" else 1
    # --status (default)
    saved = config.get("schedule") or {}
    installed = schedule_installed()
    print("Night Shift schedule status")
    print(f"- Armed: {'yes, nightly at ' + saved.get('time', '?') + ' via ' + installed if installed else 'no'}")
    print(f"- Command it runs: {nightly_command_line()}")
    snoozed = snooze_until()
    print(f"- Snooze: {'until ' + snoozed if snoozed else 'off'}")
    if LAST_NIGHTLY_PATH.exists():
        try:
            last = json.loads(LAST_NIGHTLY_PATH.read_text(encoding="utf-8"))
            print(f"- Last nightly: {last.get('when', '?')} | {last.get('status', '?')} | {last.get('detail', '')}")
        except Exception:
            pass
    pending = unreviewed_briefs()
    print(f"- Unreviewed overnight briefs: {len(pending)} (auto-pauses at {UNREVIEWED_CAP})")
    if pending:
        print(f"  Read the newest with: night-shift report --latest")
    return 0

@bind_cli
def command_snooze(args) -> int:
    if args.off:
        SNOOZE_PATH.unlink(missing_ok=True)
        print("NIGHTSHIFT_SNOOZE: GREEN | snooze off; nightly runs resume on their schedule")
        return 0
    until = None
    if args.until:
        try:
            until = datetime.strptime(args.until, "%Y-%m-%d").date()
        except ValueError:
            print("NIGHTSHIFT_SNOOZE: RED | use --until YYYY-MM-DD, --days N, or --off")
            return 2
    elif args.days:
        until = datetime.now(timezone.utc).date() + timedelta(days=args.days)
    if not until:
        current = snooze_until()
        print(f"NIGHTSHIFT_SNOOZE: GREEN | {'snoozed until ' + current if current else 'not snoozed'}")
        return 0
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SNOOZE_PATH.write_text(until.isoformat() + "\n", encoding="utf-8")
    print(f"NIGHTSHIFT_SNOOZE: GREEN | nightly runs paused until {until.isoformat()}")
    print("Wake it early with: night-shift snooze --off")
    return 0

@bind_cli
def command_deliver(args) -> int:
    ledger = select_ledger(args, completed_only=True) if getattr(args, "latest", False) else select_ledger(args)
    if not ledger or not (ledger / "morning.md").exists():
        print("NIGHTSHIFT_DELIVER: RED | no morning brief found; run night-shift report --latest first")
        return 1
    if not args.github_issue:
        print("NIGHTSHIFT_DELIVER: RED | choose a delivery target: --github-issue")
        return 2
    if not shutil.which("gh"):
        print("NIGHTSHIFT_DELIVER: YELLOW | GitHub CLI (gh) not installed; brief stays local")
        return 1
    try:
        mode_info = json.loads((ledger / "mode.json").read_text(encoding="utf-8"))
        repo = mode_info.get("repo", "")
    except Exception:
        repo = ""
    if not repo or not Path(repo).exists():
        print("NIGHTSHIFT_DELIVER: RED | could not resolve the repo this brief belongs to")
        return 1
    auth = run_cmd(["gh", "auth", "status"], timeout=30)
    if auth.rc != 0:
        print("NIGHTSHIFT_DELIVER: YELLOW | gh is not signed in; brief stays local")
        return 1
    title = "🌙 Night Shift morning brief"
    body = (ledger / "morning.md").read_text(encoding="utf-8", errors="replace")
    body += f"\n\n---\n_Updated {datetime.now(timezone.utc).isoformat(timespec='seconds')} from ledger `{ledger.name}`. Without separately saved draft-PR consent, this digest is the only remote write._\n"
    body_file = ledger / "deliver-github-issue.md"
    body_file.write_text(body, encoding="utf-8")
    listing = run_cmd(
        ["gh", "issue", "list", "--state", "open", "--search", f'in:title "{title}"', "--json", "number,title", "--limit", "10"],
        timeout=60,
        cwd=repo,
    )
    issue_number = None
    if listing.rc == 0:
        try:
            for item in json.loads(listing.stdout or "[]"):
                if item.get("title") == title:
                    issue_number = item.get("number")
                    break
        except Exception:
            issue_number = None
    if issue_number:
        result = run_cmd(["gh", "issue", "edit", str(issue_number), "--body-file", str(body_file)], timeout=60, cwd=repo)
        action = f"updated issue #{issue_number}"
    else:
        result = run_cmd(["gh", "issue", "create", "--title", title, "--body-file", str(body_file)], timeout=60, cwd=repo)
        action = "created digest issue"
    if result.rc != 0:
        print(f"NIGHTSHIFT_DELIVER: YELLOW | gh failed: {(result.stderr or result.stdout).strip()[:200]}")
        return 1
    print(f"NIGHTSHIFT_DELIVER: GREEN | {action} | one digest issue, no code written")
    return 0

@bind_cli
def command_report(args) -> int:
    if args.ledger and args.latest:
        print("NIGHTSHIFT_REPORT: RED | use either --latest or --ledger <path>, not both")
        print("Try: night-shift report --latest")
        return 2
    if not args.ledger and not args.latest:
        print("NIGHTSHIFT_REPORT: RED | choose --latest or --ledger <path>")
        print("Try: night-shift report --latest")
        return 2
    ledger = select_ledger(args, completed_only=True) if getattr(args, "latest", False) else select_ledger(args)
    if not ledger or not ledger.exists():
        print("NIGHTSHIFT_REPORT: RED | no ledger found")
        return 1
    morning = ledger / "morning.md"
    token_report = ledger / "token-report.txt"
    artifacts = list((ledger / "artifacts").glob("*")) if (ledger / "artifacts").exists() else []
    report_status = morning_status(morning) if morning.exists() else "YELLOW"
    if report_status not in {"GREEN", "YELLOW", "RED"}:
        report_status = "YELLOW"
    print(f"NIGHTSHIFT_REPORT: {report_status} | ledger={ledger} | artifacts={len(artifacts)}")
    if morning.exists():
        print("")
        print(morning.read_text(encoding="utf-8", errors="replace").strip())
        try:
            (ledger / "REVIEWED").write_text(datetime.now(timezone.utc).isoformat(timespec="seconds") + "\n", encoding="utf-8")
        except OSError:
            pass
    else:
        print("")
        print("No morning brief yet.")
        if (ledger / "STOP").exists():
            print("This run was stopped before a final brief was written.")
        print(f"Try: night-shift stop --ledger {ledger}")
        print(f"Then check: {ledger / 'startup-gate.md'}")
    if token_report.exists():
        print("")
        print("## Token Report")
        print(token_report.read_text(encoding="utf-8", errors="replace").strip())
    return 0

@bind_cli
def command_handoff(args) -> int:
    ledger = select_ledger(args, completed_only=True) if getattr(args, "latest", False) else select_ledger(args)
    report_ledger = ledger
    portfolio_items_path = ledger / "morning-items.json" if ledger else None
    is_portfolio = bool(portfolio_items_path and portfolio_items_path.exists())
    if ledger and not is_portfolio and not (ledger / "work-queue.json").exists() and (ledger / "cycles.json").exists():
        cycles = parse_json_text((ledger / "cycles.json").read_text(encoding="utf-8"), [])
        child_ledgers = [Path(row.get("ledger", "")) for row in reversed(cycles) if row.get("ledger")]
        ledger = next((child for child in child_ledgers if (child / "work-queue.json").exists()), ledger)
        report_ledger = ledger
    queue_path = portfolio_items_path if is_portfolio else ledger / "work-queue.json" if ledger else None
    if not ledger or not queue_path or not queue_path.exists():
        print("NIGHTSHIFT_HANDOFF: RED | no ranked work queue found; choose a completed run")
        return 1
    try:
        items = json.loads(queue_path.read_text(encoding="utf-8"))
        if is_portfolio:
            if args.item < 1 or args.item > len(items):
                raise ValueError(f"item {args.item} does not exist")
            item = dict(items[args.item - 1])
            verification = item.get("verification")
            if verification and not item.get("tests") and not item.get("verification_commands"):
                if isinstance(verification, list):
                    item["verification_commands"] = verification
                else:
                    item["tests"] = verification
            item = select_handoff_item([item], 1)
        else:
            item = select_handoff_item(items, args.item)
        source_ledger = ledger
        if is_portfolio:
            child_value = str(item.get("child_ledger") or "").strip()
            if child_value:
                candidate_ledger = Path(child_value).expanduser().resolve()
                if candidate_ledger.is_dir():
                    source_ledger = candidate_ledger
        mode_path = source_ledger / "mode.json"
        if not mode_path.exists() and report_ledger and report_ledger != source_ledger:
            mode_path = report_ledger / "mode.json"
        mode = json.loads(mode_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"NIGHTSHIFT_HANDOFF: RED | {str(exc)[:200]}")
        return 1
    repo = repo_root(str(mode.get("repo") or item.get("repo_path") or ""))
    if not repo or not repo.is_dir():
        print("NIGHTSHIFT_HANDOFF: RED | the handoff repository is unavailable")
        return 1

    handoff_dir = report_ledger / "handoff"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    prompt = redact(build_handoff_prompt(item, repo, report_ledger.name))
    prompt_path = handoff_dir / f"item-{args.item}-{args.agent}-prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    pack_dir = handoff_dir / f"item-{args.item}-{args.agent}-pack"
    if pack_dir.exists():
        shutil.rmtree(pack_dir)
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack_manifest_path = handoff_dir / f"item-{args.item}-{args.agent}-pack.json"
    source_ref = str(item.get("source_ref") or "")
    if source_ref:
        if not re.fullmatch(r"[0-9a-f]{40}", source_ref):
            print("NIGHTSHIFT_HANDOFF: RED | the pinned candidate revision is not an exact commit SHA")
            return 1
        pinned = run_cmd(["git", "cat-file", "-e", f"{source_ref}^{{commit}}"], cwd=repo, timeout=30)
        if pinned.rc != 0:
            print("NIGHTSHIFT_HANDOFF: RED | the pinned candidate revision is unavailable")
            print("Fetch the repository's recent history, then rerun the handoff.")
            return 1

    copied = materialize_review_files(repo, pack_dir, item.get("files") or [], source_ref)
    if not copied:
        print("NIGHTSHIFT_HANDOFF: RED | no safe committed review files could be materialized")
        return 1
    pack_metrics = handoff_pack_metrics(prompt, pack_dir, copied)
    privacy_reasons = handoff_pack_privacy_reasons(prompt, pack_dir, copied, repo)
    pack_manifest = {
        "agent": args.agent,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "item": args.item,
        "materialized_files": copied,
        "file_sha256": handoff_pack_file_hashes(pack_dir, copied),
        **pack_metrics,
        "privacy": "GREEN" if not privacy_reasons else "RED",
        "privacy_reasons": privacy_reasons,
        "sent": False,
        "source_ref": source_ref or "HEAD",
    }
    pack_manifest_path.write_text(json.dumps(pack_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if privacy_reasons:
        print(
            "NIGHTSHIFT_HANDOFF: RED | bounded pack failed privacy validation: "
            + "; ".join(privacy_reasons)[:240]
        )
        return 1
    preflight_reasons = cloud_preflight_reasons(
        args.agent,
        source_ref,
        bool(shutil.which(args.agent)),
        copied,
        privacy_reasons,
    )
    print(f"NIGHTSHIFT_HANDOFF: GREEN | prepared item={args.item} | agent={args.agent} | prompt={prompt_path}")
    print(
        "Handoff pack: "
        f"files={pack_metrics['materialized_file_count']} "
        f"bytes={pack_metrics['materialized_bytes']} "
        f"prompt_bytes={pack_metrics['prompt_bytes']} "
        f"redactions={pack_metrics['redaction_markers']} privacy=GREEN"
    )
    print(f"Review pack: {pack_dir} | manifest={pack_manifest_path}")
    if preflight_reasons:
        print("CLOUD_PREFLIGHT: RED | " + "; ".join(preflight_reasons)[:300])
        if not shutil.which(args.agent):
            print(f"Install the {args.agent} CLI and make sure it is on PATH, then rerun this command.")
    else:
        print("CLOUD_PREFLIGHT: GREEN | exact revision pinned, agent available, bounded pack passed privacy checks")
    if not args.run:
        print("Nothing was sent. Review the saved pack first; add --run --allow-cloud only if you explicitly approve this one review.")
        return 0

    cloud_allowed = bool(args.allow_cloud)
    if not cloud_allowed:
        print("NIGHTSHIFT_HANDOFF: RED | cloud use was not approved; rerun with --allow-cloud for this one review")
        return 2
    if preflight_reasons:
        print("NIGHTSHIFT_HANDOFF: RED | cloud preflight failed: " + "; ".join(preflight_reasons)[:300])
        return 1
    with tempfile.TemporaryDirectory(prefix="night-shift-handoff-") as temporary:
        review_root = Path(temporary)
        for relative in copied:
            destination = review_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pack_dir / relative, destination)
        review_started = time.monotonic()
        result = run_cmd(
            review_agent_command(args.agent, prompt, review_root),
            cwd=review_root,
            timeout=args.timeout,
        )
        review_seconds = round(time.monotonic() - review_started, 3)
    output_path = handoff_dir / f"item-{args.item}-{args.agent}-review.md"
    output_path.write_text(redact(result.stdout or result.stderr).strip() + "\n", encoding="utf-8")
    review_output = redact(result.stdout or result.stderr).strip()
    review_reasons = (
        validate_handoff_review(review_output, repo, source_ref, copied)
        if result.rc == 0 else ["coding agent command failed"]
    )
    pack_manifest.update({
        "cloud_authorized": True,
        "review_completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "review_output_bytes": len(review_output.encode("utf-8")),
        "review_seconds": review_seconds,
        "sent": True,
        "valid_review": not review_reasons,
        "validation_reasons": review_reasons,
    })
    pack_manifest_path.write_text(json.dumps(pack_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metadata = {
        "agent": args.agent,
        "cloud_authorized": True,
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "item": args.item,
        "source_ledger": str(source_ledger),
        "materialized_files": copied,
        **pack_metrics,
        "read_only": True,
        "review_output_bytes": len(review_output.encode("utf-8")),
        "review_seconds": review_seconds,
        "return_code": result.rc,
        "source_ref": source_ref,
        "valid_review": not review_reasons,
        "utility_valid": not review_reasons,
        "ready_for_implementation": handoff_review_ready(review_output) if result.rc == 0 else False,
        "utility_schema": 2,
        "validation_reasons": review_reasons,
    }
    (handoff_dir / f"item-{args.item}-{args.agent}.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if result.rc != 0 or review_reasons:
        detail = "; ".join(review_reasons)[:240]
        print(f"NIGHTSHIFT_HANDOFF: YELLOW | coding-agent review was not usable: {detail} | output={output_path}")
        return 1
    outcome = {
        "created_at": metadata["completed_at"],
        "fingerprint": str(item.get("fingerprint") or ""),
        "ledger": str(report_ledger),
        "repo": str(repo),
        "source_ref": source_ref,
        "valid_review": True,
        "ready_for_implementation": handoff_review_ready(review_output),
        "utility_valid": True,
        "utility_schema": 2,
        "verdict": handoff_review_verdict(review_output),
    }
    persistence_reason = handoff_outcome_persistence_reason(
        outcome["fingerprint"], outcome["source_ref"], outcome["verdict"]
    )
    metadata["outcome_recorded"] = not persistence_reason
    metadata["outcome_persistence_reason"] = persistence_reason
    linked_feedback = {}
    linked_repo_outcome = {}
    (handoff_dir / f"item-{args.item}-{args.agent}.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not persistence_reason:
        existing = load_review_outcomes()
        outcome["item"] = args.item
        if should_record_review_outcome(existing, outcome):
            append_review_outcome(REVIEW_OUTCOMES_PATH, outcome, existing)
        linked_feedback = link_review_to_feedback_event(FEEDBACK_PATH, outcome)
        linked_repo_outcome = link_review_to_repo_outcome(REPO_OUTCOMES_PATH, linked_feedback, outcome)
        metadata["feedback_review_linked"] = bool(linked_feedback)
        metadata["repo_outcome_review_linked"] = bool(linked_repo_outcome)
        (handoff_dir / f"item-{args.item}-{args.agent}.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if persistence_reason:
        print(
            "NIGHTSHIFT_HANDOFF: YELLOW | independent read-only review complete; "
            f"learning was not recorded ({persistence_reason}) | output={output_path}"
        )
    else:
        print(f"NIGHTSHIFT_HANDOFF: GREEN | independent read-only review complete | output={output_path}")
    return 0

@bind_cli
def command_feedback(args) -> int:
    if getattr(args, "interactive", False):
        if args.useful or args.not_useful:
            print("NIGHTSHIFT_FEEDBACK: RED | interactive mode cannot be combined with --useful or --not-useful")
            return 2
        if not collect_interactive_feedback(args):
            return 2
    if args.useful == args.not_useful:
        print("NIGHTSHIFT_FEEDBACK: RED | choose exactly one of --useful or --not-useful")
        return 2
    if args.item < 1:
        print("NIGHTSHIFT_FEEDBACK: RED | --item must be 1 or greater")
        return 2
    clarity = getattr(args, "clarity", "") or ""
    effort = getattr(args, "effort", "") or ""
    human_outcome = getattr(args, "outcome", "") or ""
    if clarity and clarity not in CLARITY_VALUES:
        print("NIGHTSHIFT_FEEDBACK: RED | --clarity must be clear or confusing")
        return 2
    if effort and effort not in EFFORT_VALUES:
        print("NIGHTSHIFT_FEEDBACK: RED | --effort must be quick, some-work, or too-much")
        return 2
    if human_outcome and human_outcome not in HUMAN_OUTCOME_VALUES:
        print("NIGHTSHIFT_FEEDBACK: RED | --outcome must be accepted, revised, or rejected")
        return 2
    if human_outcome in {"accepted", "revised"} and not args.useful:
        print("NIGHTSHIFT_FEEDBACK: RED | accepted or revised outcomes need --useful")
        return 2
    if human_outcome == "rejected" and not args.not_useful:
        print("NIGHTSHIFT_FEEDBACK: RED | rejected outcomes need --not-useful")
        return 2
    ledger = select_ledger(args, completed_only=True) if getattr(args, "latest", False) else select_ledger(args)
    morning_path = ledger / "morning-items.json" if ledger else None
    queue_path = (
        morning_path if morning_path and morning_path.exists()
        else ledger / "work-queue.json" if ledger else None
    )
    if not ledger or not queue_path or not queue_path.exists():
        print("NIGHTSHIFT_FEEDBACK: RED | no work queue found; use --latest or --ledger <path>")
        return 1
    try:
        items = json.loads(queue_path.read_text(encoding="utf-8"))
        item = items[args.item - 1]
    except (ValueError, IndexError, TypeError, json.JSONDecodeError):
        print(f"NIGHTSHIFT_FEEDBACK: RED | item {args.item} does not exist in {queue_path}")
        return 1
    try:
        mode = json.loads((ledger / "mode.json").read_text(encoding="utf-8"))
    except Exception:
        mode = {}
    outcome_repo = str(item.get("repo") or "").strip()
    if not outcome_repo:
        source_repo = repo_root(str(mode.get("repo") or ""))
        outcome_repo = repo_slug(source_repo) or str(mode.get("repo") or "")
    verdict = "useful" if args.useful else "not-useful"
    labels = item.get("labels") or []
    family = item.get("family") or task_family(
        labels[0] if labels else str(item.get("key", "")).split(":", 1)[0]
    )
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row = {
        "created_at": created_at,
        "repo": item.get("repo_path") or item.get("repo") or mode.get("repo", ""),
        "ledger": str(ledger),
        "child_ledger": item.get("child_ledger", ""),
        "rank": args.item,
        "key": item.get("key", ""),
        "family": family,
        "fingerprint": item.get("fingerprint", ""),
        "source_ref": item.get("source_ref", ""),
        "summary": item.get("summary", ""),
        "verdict": verdict,
        "note": args.note or "",
        "outcome_status": str(item.get("outcome_status") or ""),
    }
    if clarity:
        row["clarity"] = clarity
    if effort:
        row["effort"] = effort
    if human_outcome:
        row["human_outcome"] = human_outcome
    try:
        reviewed_at = (ledger / "REVIEWED").read_text(encoding="utf-8").strip()
    except OSError:
        reviewed_at = ""
    delay = feedback_delay_seconds(reviewed_at, created_at)
    if delay is not None:
        row["feedback_delay_seconds"] = delay
    review = latest_verified_review_for_candidate(
        load_review_outcomes(), str(ledger), args.item,
        str(row.get("fingerprint") or ""), str(row.get("source_ref") or ""),
    )
    if review:
        row["review_verdict"] = review["verdict"]
        row["review_verified"] = True
    existing = load_feedback()
    if not should_record_feedback_event(existing, row):
        print(
            f"NIGHTSHIFT_FEEDBACK: GREEN | item={args.item} | verdict={verdict} | "
            "already saved; no duplicate vote added"
        )
        return 0
    append_feedback_event(FEEDBACK_PATH, row)
    if outcome_repo:
        feedback_id = "|".join(
            str(row.get(field) or "")
            for field in ("ledger", "rank", "fingerprint", "verdict", "human_outcome")
        )
        append_repo_outcome(REPO_OUTCOMES_PATH, {
            "completed_at": created_at,
            "feedback_not_useful": 1 if verdict == "not-useful" else 0,
            "feedback_useful": 1 if verdict == "useful" else 0,
            "feedback_id": feedback_id,
            "kind": "feedback",
            "repo": outcome_repo,
            "source_ref": row["source_ref"],
            "feedback_outcome_status": row["outcome_status"],
            "feedback_review_verdict": row.get("review_verdict", ""),
            "feedback_verified": int(
                row.get("review_verified")
                or row["outcome_status"] in {"PROVEN_REPAIR", "VERIFIED_DRAFT"}
            ),
            "human_outcome": human_outcome,
            "human_outcome_accepted": int(human_outcome == "accepted"),
            "human_outcome_revised": int(human_outcome == "revised"),
            "human_outcome_rejected": int(human_outcome == "rejected"),
        })
    print(f"NIGHTSHIFT_FEEDBACK: GREEN | item={args.item} | verdict={verdict} | saved={FEEDBACK_PATH}")
    print("Night Shift will use this signal when ranking future work and choosing which repos get time.")
    return 0

@bind_cli
def command_stop(args) -> int:
    if args.ledger and args.latest:
        print("NIGHTSHIFT_STOP: RED | use either --latest or --ledger <path>, not both")
        print("Try: night-shift stop --latest")
        return 2
    if not args.ledger and not args.latest:
        print("NIGHTSHIFT_STOP: RED | choose --latest or --ledger <path>")
        print("Try: night-shift stop --latest")
        return 2
    ledger = select_ledger(args)
    if not ledger or not ledger.exists():
        print("NIGHTSHIFT_STOP: RED | no ledger found")
        return 1
    stop_file = ledger / "STOP"
    stop_file.write_text(f"stop requested at {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n", encoding="utf-8")
    stopped, missing = stop_recorded_processes(ledger)
    autopilot_signaled = False
    try:
        active = parse_json_text(AUTOPILOT_STATE_PATH.read_text(encoding="utf-8"), {})
        active_ledger = Path(active.get("ledger", ""))
        if active_ledger.exists():
            (active_ledger / "STOP").write_text(
                f"stop requested at {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n",
                encoding="utf-8",
            )
            autopilot_signaled = True
    except OSError:
        pass
    print(
        f"NIGHTSHIFT_STOP: GREEN | stop file written | signaled={stopped} | already_gone={missing} "
        f"| autopilot={'yes' if autopilot_signaled else 'no'} | ledger={ledger}"
    )
    return 0

