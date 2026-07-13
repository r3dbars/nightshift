# Issue Evidence Consistency Proof

Date: 2026-07-12

## Claim

Issue-review prompts can produce consistent, source-bounded candidates without
weakening evidence validation or touching the source checkout.

## Change

Issue tasks now receive a dedicated evidence contract:

- exactly one `path:line | exact source line` citation;
- a claim limited to that literal source line;
- issue context belongs in `WHY_NOW`;
- diagnosis and fix language remains a hypothesis to verify.

The validator also rejects claims of intentional or deliberate behavior unless
the cited source line explicitly supports that intent.

## Live Trials

Three independent runs used empty Night Shift homes, the real `r3dbars/Draft`
checkout, a one-task limit, and the live Windows worker.

All three runs:

- selected open issue #38;
- ranked `Sources/Speech/ParakeetEngine.swift` first;
- cited line 51: `private let liveDisplayEnabled = false`;
- produced one validator-clean `MAYBE` candidate;
- left the original checkout clean;
- created no patch, PR, merge, deploy, or release.

Efficiency:

- Two trials passed on the first Windows call at 3,841 and 3,799 tokens.
- One trial needed the bounded correction and used 7,912 tokens.
- Acceptance: 3/3.
- First-pass acceptance: 2/3.
- Average tokens per accepted candidate: about 5,184, down from about 7,700.

This proves more consistent review candidates, not a verified fix. Draft still
has no approved Night Shift execution profile, and live audio behavior was not
tested.

## Deterministic Gate

The package gate passes 168 tests. Focused coverage proves the issue-only prompt
contract, enforces exactly one issue citation, and rejects unsupported or
polarity-mismatched intent claims while preserving strict path, command, and
pinned-revision checks.
