# Portfolio Learning Real Run

This is a real three-repository replay after the legacy feedback bridge and
plain-language selection reason landed on current main.

## Run

- Source revision: `9d86fbb`
- Scope: live authenticated GitHub portfolio, maximum three repositories
- Repositories visited: `r3dbars/BetterFeedback`, `r3dbars/nightshift`, and `r3dbars/transcripted`
- Compute route: Mac-local only; no Windows or cloud calls
- Permission: `brief`; no patch execution and no GitHub writes
- Isolated copied state: `/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/tmp.yYYYLZIWtM`
- Parent ledger: `/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/tmp.yYYYLZIWtM/maestro/overnight/night-shift-20260714T001227Z-autopilot`

## What the run proved

- All three owner-validated repositories got clean cached checkouts or the
  read-only primary checkout.
- Deterministic filters found no model-ready task in any child run, so the
  run spent zero model tokens and produced no speculative patch.
- The saved useful vote for the Night Shift checkout was an older path-based
  feedback record. The compatibility bridge resolved it to `r3dbars/nightshift`.
- `r3dbars/nightshift` received `outcome_adjustment: 50`, with
  `useful_feedback: 1`, `productive_runs: 5`, and `recent_runs: 8`.
- The resulting scores were BetterFeedback `590`, Night Shift `170`, and
  Transcripted `122`; Night Shift ranked ahead of Transcripted after the
  learned adjustment.
- The morning brief explained the choice as:
  `your current project; you marked recent work here useful`.
- The closeout stayed honest: `NIGHTSHIFT_AUTOPILOT: YELLOW`, because no
  evidence-backed task survived to become a useful morning choice.

This supports live multi-repo discovery, durable feedback compatibility,
learned portfolio ranking, zero-token filtering, and a transparent morning
reason. It does not prove repeated accepted patches, human comprehension, or
multi-night outcome lift, so those scores remain below 95.
