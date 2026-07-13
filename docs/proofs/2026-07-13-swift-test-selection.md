# Swift Test Selection Lab

This lab checks whether Night Shift can use ordinary Swift/XCTest coverage
without treating an unreachable macOS app target as patchable.

## Evidence

- Repository: `r3dbars/Unspool`
- Revision: `44fbabcc91724aaf744588b96c918c11bebe1d23`
- Verification command: `swift test`
- Normal mode: coverage-only Swift gaps stayed skipped, as designed.
- Bounded afterburner: a Swift coverage candidate reached the local model in
  3,586 estimated tokens.
- The first candidate was an `AppDelegate` under `Sources/Unspool`, but the
  existing tests import `UnspoolCore`; the new source-module guard excluded
  that unreachable executable target before another model call.
- The next candidate was `AppSettings` under `Sources/UnspoolCore`, which the
  tests can import. It reached an isolated draft attempt, but the worker tried
  to create a new test file outside the approved existing test path. The
  deterministic patch boundary rejected it.
- Source checkout remained clean. No patch or PR was created.

## Night Shift changes proven by this lab

- Swift invocation evidence is limited to existing Swift test files.
- Swift declarations and comments do not count as calls.
- A Swift source becomes patchable only when its module is imported by the
  existing test corpus.
- A rejected Swift patch is reported as rejected, not as useful output.

## Package proof

`bash scripts/check-package.sh` passed with 394 tests.
