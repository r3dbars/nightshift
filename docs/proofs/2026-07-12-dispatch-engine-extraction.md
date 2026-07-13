# Dispatch Engine Extraction Proof

Date: 2026-07-12

## Claim

Night Shift model dispatch, correction retry, artifact capture, and token
accounting now have one directly tested engine without changing observable
dispatch results.

## Change

`bin/night_shift_dispatch.py` now owns:

- correction prompts with exact allowed paths, citations, and commands;
- evidence-gated Mac and Windows correction retries;
- explicit-reject and unsafe-approval retry suppression;
- best-attempt selection;
- delegate invocation, timeout propagation, and process-ledger wiring;
- per-attempt and selected artifacts with redaction;
- proof collection and cross-attempt token aggregation;
- the complete normalized dispatch result.

The controller retains a thin wrapper that injects its command runner, delegate
path, copied environment, mode limits, and proof readers. It fell from 4,151 to
3,998 lines. The engine imports only leaf policy modules and has no circular
dependency on the controller.

## Exact Dispatch Parity

The pre-change and current controllers were loaded side by side with identical
deterministic transports.

Correction case:

- First result: rejected but repairable.
- Second result: validator-clean candidate.
- Old/new normalized result parity: yes.
- Retry count: 1.
- Aggregated tokens: 20.
- Selected return code: 0.

Timeout case:

- Return code: 124.
- Timed out: true.
- Retry count: 0.
- Aggregated tokens: 10.
- Old/new normalized result parity: yes.

Elapsed seconds and absolute ledger directories were normalized before
comparison; all behavioral output fields were compared exactly.

## Deterministic Gate

`scripts/check-package.sh` passed all 217 tests and package/install checks.
Fifteen direct dispatch tests cover retry/no-retry decisions, unsafe output,
explicit reject, timeout propagation, result keys, artifact names/content,
environment defaults, token aggregation, citation generation, evidence gates,
and attempt tie-breaking.

## Regrade

Maintainability moves from 82 to 87. Queue construction and dispatch now have
cohesive tested owners, but run/autopilot lifecycle orchestration remains in the
3,998-line controller. Runtime reliability remains 86 because deterministic
parity is not crash-recovery or long-soak integration proof.
