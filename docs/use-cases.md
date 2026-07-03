# 20 Night Shift Use Cases

Use these as starting points. Each one should end in a morning brief, artifacts,
and a clear next action, not surprise merges or releases.

1. **Solo Mac developer with LM Studio**
   - Start: `quiet` for a short pass, `night-shift` for overnight.
   - Ask for: TODO mining, test-gap maps, docs drift, small patch plans.
   - Morning output: ranked artifacts and one or two safe follow-up tasks.

2. **Mac plus a Windows GPU box**
   - Start: `night-shift`; use `afterburner` only when heat and time are fine.
   - Ask for: Mac local triage plus deeper Windows review and test planning.
   - Morning output: separate local and Windows artifacts with token totals.

3. **Windows worker only**
   - Start: `quiet --max-local 0`.
   - Ask for: draft implementation plans, review notes, fixture ideas.
   - Morning output: Windows drafts that Codex or a human must verify.

4. **No local model installed yet**
   - Start: `doctor`, then `plan`.
   - Ask for: setup blockers and a repo plan.
   - Morning output: no worker claims, just exact next setup steps.

5. **Privacy-sensitive repo**
   - Start: `quiet` with local lanes only.
   - Ask for: coarse code maps, test gaps, and docs checks.
   - Morning output: local-only artifacts; no private text pasted to cloud lanes.

6. **Maintainer with a stale issue backlog**
   - Start: `night-shift`.
   - Ask for: issue dedupe, labels, suspected owners, and close/keep candidates.
   - Morning output: a triage list and polished issue-comment drafts.

7. **Maintainer with a messy PR queue**
   - Start: `night-shift`.
   - Ask for: classify PRs as merge, hold, superseded, close, or cherry-pick.
   - Morning output: PR-by-PR notes with proof links and risks.

8. **Open-source docs cleanup**
   - Start: `quiet`.
   - Ask for: stale commands, missing setup steps, broken examples, drift.
   - Morning output: a small docs patch plan or one narrow draft PR candidate.

9. **Test generation push**
   - Start: `night-shift`.
   - Ask for: changed-file coverage gaps, fixture ideas, and exact test commands.
   - Morning output: proposed tests, expected assertions, and files to touch.

10. **Release-readiness check**
    - Start: `quiet`.
    - Ask for: release notes, blockers, risky changes, and manual QA still needed.
    - Morning output: a readiness brief. Night Shift does not publish anything.

11. **Bug triage before work starts**
    - Start: `quiet`.
    - Ask for: cluster logs or issue text by suspected subsystem.
    - Morning output: top bug families, repro hints, and owner suggestions.

12. **Sentry or error-family audit**
    - Start: `quiet`.
    - Ask for: issue families, likely files, missing tests, and repro paths.
    - Morning output: fix candidates without claiming production proof.

13. **Analytics or product-instrumentation audit**
    - Start: `night-shift`.
    - Ask for: event gaps, property drift, funnel blind spots, dashboard questions.
    - Morning output: measurement gaps and safe follow-up issues.

14. **Refactor exploration**
    - Start: `night-shift`; optionally allow one Claude reasoning pass.
    - Ask for: oversized files, duplicated patterns, unclear boundaries.
    - Morning output: ranked candidates. Do not rewrite the architecture overnight.

15. **Claude budget control**
    - Start: `night-shift` with Claude reserved for one hard question.
    - Ask for: cheap local/Windows scans first, Claude only for the risk call.
    - Morning output: one Claude-backed decision note plus cheaper lane artifacts.

16. **Codex budget control**
    - Start: local and Windows lanes for draft work.
    - Ask for: maps, reviews, plans, and tests that Codex can verify later.
    - Morning output: fewer Codex turns spent on exploration, more on proof.

17. **Morning triage ritual**
    - Start: `report --latest`.
    - Ask for: top action, kept artifacts, rejected artifacts, and unknowns.
    - Morning output: one first move instead of a pile of raw worker output.

18. **Multi-repo operator**
    - Start: one Night Shift run per repo.
    - Ask for: separate ledgers, separate boards, separate morning briefs.
    - Morning output: clean repo-by-repo decisions instead of mixed context.

19. **Low-heat laptop night**
    - Start: `quiet --max-parallel-local 1 --max-windows 0`.
    - Ask for: read-only scans and compact summaries.
    - Morning output: useful notes without trying to keep the machine busy.

20. **Afterburner / tokenmaxx run**
    - Start: `afterburner` only when you want to spend idle local compute hard.
    - Ask for: many maps, audits, rankings, and patch plans.
    - Morning output: high-volume artifacts, strict KEEP/MAYBE/REJECT scoring, and
      still no autonomous merge or release.

Each recipe above pairs with the copy-paste commands in
[`skills/night-shift/examples`](../skills/night-shift/examples) and the full
[user guide](guide.md).
