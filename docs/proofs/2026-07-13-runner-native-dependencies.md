# Runner-Native Dependency And Draft Proof

This proof covers a real Linux-container verification run from macOS against a
fresh clone of `r3dbars/BetterFeedback`.

## Dependency preparation

The host checkout had macOS-native `node_modules`, which cannot be trusted in
the Linux runner. Night Shift prepared a separate cache inside a disposable,
networked container with:

- read-only source input and a writable dependency output only;
- no credentials, `.npmrc`, lifecycle scripts, audit, or fund calls;
- bounded CPU, memory, process count, and temporary storage;
- `npm ci --ignore-scripts` followed by Prisma client generation when needed.

The cache marker binds the dependency tree to the approved remote, immutable
runner image, and lockfile digest. A later trust run reused that exact cache
automatically and passed the approved `npm run test:unit:vitest` preflight.

## Live local-model draft

The fresh disposable run used the Mac-local `qwen/qwen3-coder-next` model and
selected the real `formatPercent` test gap from BetterFeedback. It generated a
one-file patch, applied it only in a disposable worktree, and passed the real
repository test command in the isolated runner:

```text
NIGHTSHIFT_RUN: YELLOW | mode=quiet | local=3 | windows=0 | tokens=12916
status: VERIFIED_DRAFT
baseline_rc: 0
after_rc: 0
files: tests/unit/lib/analytics-metrics.test.ts
verification: npm run test:unit:vitest
worktree_removed: true
```

The first live attempt asserted the wrong JavaScript negative-zero behavior and
was rejected. The bounded repair call then corrected that failure; it was
limited to 2,048 output tokens so the verification prompt could not overflow
the local model context. The original source checkout stayed clean throughout.

Artifacts:

```text
/Users/redbars/.codex/maestro/overnight/night-shift-betterfeedback-rerun-codex/maestro/overnight/night-shift-20260713T182522Z-autopilot/drafts/r3dbars--BetterFeedback/changed-file-proof-02-app-analytics-analytics-metrics-ts-tests-draft-pr-candidat.json
/Users/redbars/.codex/maestro/overnight/night-shift-betterfeedback-rerun-codex/maestro/overnight/night-shift-20260713T182522Z-autopilot/drafts/r3dbars--BetterFeedback/changed-file-proof-02-app-analytics-analytics-metrics-ts-tests-draft-pr-candidat-sandbox/runner.txt
```
