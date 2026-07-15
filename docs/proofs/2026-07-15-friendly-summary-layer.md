# Friendly Morning Summary Layer

This change keeps worker summaries exact for evidence while giving a first-time
reader a shorter plain-English sentence when a summary starts with common
code-review wording such as `The \`method\` method in \`Owner\` returns ...`.

## Behavior

- The first action and numbered morning choices use the friendly sentence.
- The original redacted summary remains below it as `Technical detail:`.
- Portfolio morning choices use the same wording helper.
- Summaries that are already plain enough are unchanged.
- Ranking, evidence, dispatch, privacy, and score rules are unchanged.

## Proof

- Focused reporting suite: `27 tests, OK`.
- Full package gate: `487 tests, OK`.
- Gate command: `bash scripts/check-package.sh`.
- No score increased from this change. Morning UX remains `94/95` until a
  real human comprehension and review-effort study provides direct evidence.
