---
name: night-shift
description: Put idle local AI to useful work across recently active repositories overnight. Use for first-time setup, "run Night Shift," bedtime launches, morning reports, stopping a shift, schedules, local or LAN model setup, and ClaudeBrain raw intake.
---

# Night Shift

Night Shift is the bedtime button for useful repo work.

The normal experience is:

1. The user says `/night-shift` or asks to run Night Shift.
2. Detect the current repo, recently active owned GitHub repos, local AI, a
   configured LAN worker, the sandbox, and power state.
3. On first use, show one short plan and ask one question: start it?
4. On later nights, use the saved plan unless the user asks for a change.
5. In the morning, lead with verified outcomes and draft PRs, not logs.

Do not turn normal setup into a questionnaire. Never ask for a repo path, model
name, server URL, GitHub identity, test command, or machine detail that can be
detected safely.

When the user is exploring and has not yet said to start, run this non-writing
preview first:

```bash
night-shift start --dry-run --yes
```

Summarize that exact preview and ask `Start the shift?` once. If they say yes,
run `night-shift start --yes`. If they already said "run it," "goodnight," or
equivalent, that is the confirmation; do not make them approve the same plan
twice.

## Default Night

The first-run default is intentionally useful:

- recently active owned GitHub repos when GitHub is available, otherwise the
  current repo;
- Mac-local AI, plus a previously configured private LAN worker when healthy;
- Normal mode for eight hours;
- hands-on autonomy: isolated patches, repeated approved checks, and bounded
  draft PRs when the repo passes every ownership and safety gate;
- no cloud model unless the user explicitly allows it.

Say this plainly:

```text
Welcome to Night Shift. I found your projects and local AI.

Tonight I will look for small work that is actually worth doing: failing tests,
missing unit or E2E coverage, stale docs, narrow issue fixes, and exact code
cleanup. I will work in disposable copies, rerun approved checks, and leave a
short morning brief. I may open a tested draft PR for review, but I will never
merge, deploy, release, touch secrets, or edit your checkout.

Start the eight-hour shift?
```

When the user already said "run it," "goodnight," or equivalent, that is the
start request. Do not ask them to repeat it. Run:

```bash
night-shift start --yes
```

Use `night-shift start --advanced` only when the user asks to customize scope,
privacy, autonomy, compute, goals, or stop time.

## Useful Work

Night Shift should prefer work in this order:

1. **Repair:** a pinned failing CI or deterministic test with a real assertion
   failure.
2. **Finish:** a source-grounded open issue with a narrow fix and an approved
   check.
3. **Strengthen:** a missing unit test or one existing E2E journey.
4. **Clarify:** a stale setup, test, quickstart, or report command in docs.
5. **Clean up:** one exact duplicate, dead private helper, or redundant branch
   in a recently changed source file.
6. **Understand:** report-only maps and audits when no patch is safe.

Models do not choose their own authority. The controller assigns a trusted
intent before dispatch. That intent fixes allowed file types, patch size,
baseline requirements, verification command, and publication rules.

## Proof Rules

A model answer is only a candidate. A preserved draft must have:

- exact repo-relative files from supplied evidence;
- an exact source commit;
- a diff within the intent's file and line limits;
- no new dependencies, workflows, config, generated files, migrations,
  credentials, network/process/environment access, or release behavior;
- the same approved no-network sandbox command run twice before editing;
- the finished patch passing twice, or three times for E2E work.

Only the same classified assertion failure reproduced twice and then fixed is
called `PROVEN_REPAIR`. Clean-baseline docs, tests, issue fixes, and cleanup are
`VERIFIED_DRAFT`. Infrastructure errors, missing tools, skipped checks, and
flaky results are never proof.

## Draft PR Rules

After the user's saved hands-on consent, Night Shift may open a draft PR only
when all of these are true:

- GitHub proves the signed-in user owns the non-fork repo;
- an external approval bound to the exact remote exists;
- the source SHA is on the fetched default branch;
- host Git hooks, custom filters, and executable diff drivers are absent;
- `pull_request_target` and external CI configs do not make same-repo
  publication unsafe;
- the patch passes fresh repeated sandbox checks again.

The commit skips hosted CI and the PR stays draft. Limit publication to one PR
per repo and three per shift. Additional verified patches stay local for the
morning. Never merge, force-push, deploy, release, publish, tag, notarize,
change visibility, or change credentials or billing.

If publication is unsafe, keep the verified patch local and explain why. That
is a useful result, not a failed night.

## Morning

If a shift is active, stop it only when the user asks or its deadline has
arrived. Then run:

```bash
night-shift report --latest
```

Lead with:

1. draft PRs opened;
2. verified local patches;
3. the best source-grounded candidate;
4. blockers that prevented execution.

For each useful result, state the repo, what changed, files, verification,
proof level, and PR or patch path. Keep candidates separate from verified
work. End with one recommendation for the user's cloud coding agent or human
review.

Record feedback when the user gives it:

```bash
night-shift feedback --latest --item 1 --useful
night-shift feedback --latest --item 1 --not-useful --note "too generic"
```

## Other Commands

```bash
night-shift health
night-shift stop --latest
night-shift schedule --nightly 23:30
night-shift schedule --status
night-shift snooze --days 7
night-shift trust-repo --repo /path --apply
```

`trust-repo` is normally prepared automatically after the user's one hands-on
consent. Use it directly to preview or repair one repo's approval.

## ClaudeBrain Raw Intake

For ClaudeBrain, keep all content local:

```bash
night-shift brain-intake --vault /Users/redbars/Documents/claudebrain
```

It reads new text files under `raw/`, writes one source-linked suggestion packet
under `raw/scraps/`, and remembers hashes. It never moves raw files or edits
authoritative memory, people, projects, notes, or archive pages.

## Hard Lines

- Never edit the user's checkout.
- Never trust an in-repo profile to authorize its own execution.
- Never run discovered repository commands on the host.
- Never send private repo or personal content to cloud lanes without consent.
- Never claim hardware, install, audio, telemetry, hosted, or manual proof that
  was not actually collected.
- Never merge or perform a release/deploy action.

Read the package `SAFETY.md` for the complete boundary and
`references/operations.md` only when debugging or changing the controller.
