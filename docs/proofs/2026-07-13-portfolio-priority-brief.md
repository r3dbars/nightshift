# Portfolio Priority Brief: 2026-07-13

## Run

- Source revision: `1c11f47` (PR #162 merged)
- Scope: `github-recent`
- Permission: `brief` (read-only)
- Mode: `quiet`
- Repositories visited: 3
- Local/Windows model calls: 0
- Ledger: `/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/tmp.8h1vqEabvd/maestro/overnight/night-shift-20260713T231249Z-autopilot`
- Result: `YELLOW`; no task had enough evidence to spend model tokens safely

## Ranking Shown To The User

1. `r3dbars/BetterFeedback` - score 590, three recent failing checks, one
   issue, and three PRs; reason shown: **recent failing checks**.
2. `r3dbars/transcripted` - score 142, two active PRs; reason shown:
   **active GitHub work**.
3. `r3dbars/nightshift` - score 120, the explicit primary repo; reason shown:
   **your current project**.

The portfolio brief preserved this ranked order instead of alphabetizing the
repos. The durable cycle rows also kept bounded score, rank, signal counts, and
the plain-language reason. All checkouts were read-only, no model tokens were
spent, no PR was opened, and the source checkout stayed clean.

## What This Proves

The system now tells a new user both **what it checked** and **why it chose
that order**, while refusing to spend AI tokens when the deterministic evidence
is too weak. This strengthens repository prioritization, portfolio discovery,
multi-repo operation, and morning clarity.

It does not prove that the highest-ranked repo produced accepted user value;
that still needs repeated useful outcomes and human review.
