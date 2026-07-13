# Normal Mode Signal Gate Proof

Date: 2026-07-12

## Claim

Normal mode no longer spends model tokens on coverage-index-only guesses unless
the user explicitly asks for test or coverage work. Afterburner still permits
that exploration. Portfolio status also matches the saved morning report.

## Baseline

A clean three-repository run attempted six coverage-index candidates, accepted
all six as `MAYBE`, produced no deterministic proof or patches, and used about
20,782 local-model tokens. Each candidate was based on zero identifier matches,
which is not enough to claim a real coverage gap.

## Rehearsal

The same three-repository scope was run from a fresh linked install and empty
task history:

```sh
night-shift autopilot --repo /Users/redbars/code/night-shift \
  --scope github-recent --active-days 14 --max-repos 3 --task-limit 6 \
  --mode night-shift --permission draft-local --guidance scan \
  --stop-after 2h --timeout 300 --once --skip-smoke
```

Results:

- BetterFeedback: 39 weak signals skipped before dispatch; one maintainer-filed
  issue evaluated and rejected; about 3,542 Windows-model tokens.
- Draft: 39 weak signals skipped; one maintainer-filed issue evaluated and
  rejected; about 2,489 Windows-model tokens.
- Night Shift: 29 weak signals skipped; zero model calls and zero tokens.
- Portfolio total: about 6,031 tokens, down 71% from the baseline.
- Portfolio terminal status: `YELLOW`.
- Portfolio morning status: `YELLOW`.
- No patch, PR, merge, release, deploy, or publication occurred.

The result proves cheaper and more honest filtering. It does not prove useful
output, so the useful-output score does not move.

## Deterministic Gate

The package gate passes 161 tests. Focused tests prove that Normal mode rejects
coverage-only tasks, Afterburner accepts them, an explicit coverage goal accepts
them, the override requires an explicit action and target, and the portfolio
brief does not repeat an unproven child claim.
