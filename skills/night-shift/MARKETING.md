# Night Shift Marketing Kit

Use this as public-facing copy for the repo, README, launch notes, or screenshots.
Keep the promise small: Night Shift creates useful overnight drafts and a morning
brief. It does not ship while you sleep.

## One-Line Positioning

Night Shift puts idle local AI compute to work overnight, then hands you
a ranked morning brief instead of a mystery pile of agent output.

## GitHub Repo Description Options

- Local-first overnight AI workbench for repo scans, draft plans, token reports,
  and a ranked morning brief.
- Put idle Mac and Windows AI compute to work while you sleep; wake up to safe
  draft artifacts and a clear next action.
- A bounded night-shift mode for AI coding agents: local workers draft, Codex or
  humans verify.

## Hero Copy Options

### Calm

Put your idle AI hardware to work while you sleep.

### Direct

Run safe repo chores overnight. Wake up to the brief.

### Slightly Fun

Let the machines take the night shift. You still keep the keys.

## Launch Narrative

Most AI coding tools are built for the moment you are actively steering them.
Night Shift is built for the hours when your laptop, desktop GPU, and
repo backlog are all sitting there unused.

You point it at a repo, choose the compute lanes that are allowed, and pick a
mode. It runs bounded local and Windows worker loops, records proof paths and
token totals, rejects weak artifacts, and writes a morning brief.

The safety boundary is the product: worker output is draft-only. Night Shift
does not merge, release, deploy, move user files, touch credentials, or claim
manual proof. It gives Codex or a human the cleanest next action.

## README Badges

Suggested badges:

```markdown
[![local-first](https://img.shields.io/badge/local--first-by_default-2ea44f)](#safety-and-privacy)
[![drafts-not-deploys](https://img.shields.io/badge/drafts-not_deploys-6f42c1)](#what-it-will-do)
[![morning-brief](https://img.shields.io/badge/output-morning_brief-0969da)](#morning-workflow)
```

Avoid badges that imply production readiness, release automation, or public
package availability until those are true.

## Visual Suggestions

- Hero image: a terminal with `night-shift run --mode night-shift` on the
  left and a clean `morning.md` summary on the right.
- Diagram: repo plus compute lanes flowing into Night Shift, then into artifacts,
  token report, morning brief, and human/Codex review.
- Screenshot: `doctor` output showing reachable lanes and honest yellow states.
- Screenshot: sample morning brief with `KEEP`, `MAYBE`, `REJECT`, token totals,
  proof paths, and the single next action.
- Social image: dark terminal desk, small status lights, headline "Let the
  machines take the night shift. You keep the keys."

## Image Prompt Placeholder

Create a clean product screenshot-style hero for a developer tool called
"Night Shift". Show a macOS terminal running `night-shift run
--repo /path/to/project --mode night-shift`, a small lane status panel for Local,
Windows, Claude, and Codex, and a morning brief panel with KEEP/MAYBE/REJECT
counts. Style: quiet developer tooling, sharp text, no mascot, no sci-fi glow,
no claims about autonomous deployment.

## Short Launch Post

Night Shift is a local-first overnight workbench for AI coding agents.

Point it at a repo, point it at your idle compute, and let local/Windows workers
spend the night making maps, audits, draft plans, and issue candidates. In the
morning, you get a ranked brief, token totals, proof paths, and a clear first
move.

It is intentionally not an autonomous release bot. Workers draft. Codex or a
human verifies.

## What To Emphasize

- Local-first by default.
- Uses compute you already have.
- Produces artifacts, not surprise changes.
- Honest about proof and manual unknowns.
- Good for repo chores that are attention-heavy but execution-safe.

## What To Avoid

- Do not say it deploys, merges, releases, or publishes while you sleep.
- Do not say it proves hardware, audio, install, or manual QA without a real
  human/device check.
- Do not imply private data is safe to send to non-local lanes.
- Do not make the repo public until the owner explicitly decides to.
