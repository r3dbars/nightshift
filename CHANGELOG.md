# Changelog

All notable package-facing changes should be recorded here.

This project uses `vMAJOR.MINOR.PATCH` tags. Pre-1.0 releases may still change
commands, ledger formats, and packaging details.

## Unreleased

- Ground worker tasks with numbered source excerpts, recent diffs, live issues,
  pull requests, failed workflows, TODOs, and detected test commands.
- Require exact evidence, files, verification commands, and expected results
  before a worker artifact can score KEEP; retry one weak response once.
- Replace generic artifact piles with at most three evidence-backed morning
  choices and judge normal runs by useful KEEP output rather than token volume.
- Add local `night-shift feedback` so useful and not-useful choices influence
  future prompts and ranking for the same repo.
- Add deterministic unit coverage for grounding, scoring, queue selection,
  evidence packs, and feedback ranking.
- Shorten the bundled skill and move detailed behavior into its existing
  references so setup and bedtime conversations stay focused.
- Add Autopilot: `night-shift schedule --nightly HH:MM` installs a standing
  nightly run (launchd/cron) that reads saved config at fire time, pauses
  itself after 3 unread morning briefs, drops to quiet mode on battery, and
  is inspectable via `schedule --status`.
- Add `night-shift snooze` (--days/--until/--off) as the vacation switch for
  the standing shift.
- Add `night-shift deliver --github-issue`: keep exactly one digest issue per
  repo updated with the latest morning brief via the gh CLI — the only repo
  write Night Shift is ever allowed, opt-in only.
- Mark briefs as reviewed when read via `night-shift report`, powering the
  attention-aware pause.
- Recenter the skill and README on the founding problem: idle AI hardware is
  free tokens; First Night now ends with the make-it-automatic offer, and the
  skill gains Autopilot and Snooze moments plus a morning surfacing contract.
- Document the automation design in `docs/autopilot.md`.
- Handle SIGPIPE cleanly so piping CLI output to `head` no longer tracebacks.
- Rewrite the README as a short, scannable front page: what you wake up to,
  a 60-second quick start, how it works, autonomy and mode tables, and hard
  boundaries. Deep material moved to `docs/guide.md` and `docs/use-cases.md`.
- Fix a stale "private/proprietary" license line that survived the MIT switch.
- Move the public home to `github.com/r3dbars/nightshift` and update install
  URLs; add a jump-to navigation line to the README.
- Go open source: replace the private license placeholder with the MIT
  license, update package docs and checks, and rework the README opening so a
  first-time visitor immediately sees what Night Shift does, what they wake up
  to, and how to install it.
- Generalize the public-launch safety guidance now that the project ships from
  a clean public repository: Night Shift still never changes any repository's
  visibility.
- Rebuild the bundled skill around a guided first-run experience: a moments
  router (First Night / Bedtime / Morning / Stop / Tune-Up), a hardware-first
  setup conversation with a consent-gated local AI scan, and onboarding
  contracts modeled on the best community skills.
- Prioritize local AI hardware in setup: scan for Apple Silicon unified
  memory, GPUs, LM Studio, and Ollama before asking about cloud subscriptions.
- Auto-detect Ollama at `localhost:11434` when LM Studio is not reachable, and
  pick the best downloaded coder/instruct model automatically.
- Add `start` flags (`--wake-goal`, `--guidance`, `--goal`, `--privacy`,
  `--permission`, `--stop-after`) so assistants can run the whole setup
  conversation in chat and persist the answers without a keyboard.
- Split the skill into a short guided SKILL.md plus reference files for
  hardware scanning, operations, and worker prompt templates.
- Add repo scans, repo-specific planned queues, deduped work queues, and autonomy levels for more useful overnight runs.
- Expand the setup wizard into a beginner-friendly setup lab.
- Add wake-up goal, privacy route, project sensitivity, guidance, and stop-timer setup questions.
- Add setup lab artifacts for readiness, providers, and routing.
- Treat missing Windows worker and GitHub/Claude lanes as optional info for Mac-only users.
- Add real chat probes, disk/write/power/recovery checks, and stop-after enforcement.
- Add troubleshooting docs for first-run setup.
- Make first-run setup checks friendlier and hide raw token-scope/auth noise from the wizard.
- Avoid setup ledger crashes when two runs start in the same second.
- Fix Python 3.9 doctor support and invalid-mode command hints.
- Rework the first-run wizard into a warmer decision-brief flow inspired by GStack Office Hours.
- Add `night-shift start`, a first-run setup wizard and safe launcher.
- Rename the public command and bundled skill to `night-shift`.
- Clarify the private/pre-license package status.
- Document package contents, install layout, and release checklist.
- Add a package check script for contributors.

## 0.1.0 - 2026-06-23

- Initial private package shape for `night-shift`.
- Includes CLI launch/report/stop commands, lane wrappers, installer, safety
  docs, and the bundled `night-shift` skill.
