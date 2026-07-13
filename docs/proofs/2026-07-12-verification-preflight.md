# Verification Command Preflight Proof

Date: 2026-07-12

## Claim

`trust-repo --apply` proves the exact displayed verification command can start
inside the immutable runner before saving execution approval. Missing runner
tooling fails closed; genuine test failures remain eligible for repair.

## Incompatible Repo

A fresh real `r3dbars/Draft` clone under the macOS home previewed and attempted
approval with its detected `bash run-tests.sh` command.

The real Docker/Colima preflight copied the read-only source into tmpfs and ran
the script. Teardown checks passed, then compilation stopped with:

```text
run-tests.sh: line 13: swiftc: command not found
```

Night Shift returned `YELLOW`, saved no approval, kept Draft analysis-only, and
left the checkout clean. This correctly exposes that the current Debian runner
does not support Draft's Swift/Xcode verification.

## Compatible Repo

A fresh real `r3dbars/nightshift` clone used the detected command:

```text
python3 -m unittest discover -s tests -p test_*.py
```

The exact command passed in the real no-network runner. Night Shift saved the
external approval at mode `0600`, reported `GREEN`, and left the clone clean.

## Classification

- Exit 0: verification is runner-compatible; approval may be saved.
- Recognized test-runner failure: approval may be saved because Night Shift can
  reproduce/repair it. This branch is covered by command-level tests; a live
  failing-repo approval rehearsal remains pending.
- Exit 125/126/127 or known mount/command/runtime failure: approval is blocked
  and nothing is saved.

## Deterministic Gate

The package gate passes 178 tests. Focused coverage separates passing checks,
recognized test failures, unknown exits, missing executables, and source-mount
failures. Command-level coverage proves blocked preflights never call the
approval writer while a recognized failing unittest can save.
