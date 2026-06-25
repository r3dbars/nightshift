# Changelog

All notable package-facing changes should be recorded here.

This project uses `vMAJOR.MINOR.PATCH` tags. Pre-1.0 releases may still change
commands, ledger formats, and packaging details.

## Unreleased

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
