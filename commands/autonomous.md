---
description: Go fully autonomous from here — make your own decisions, ship it, no more questions
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Task, TodoWrite, WebFetch, WebSearch
---

# Autonomous Mode

Andrew is handing off and going AFK. From this point onward, **operate fully
autonomously**. He trusts your judgement and you can always iterate again later.

**Optional context / goal refinement:** $ARGUMENTS

## The mandate

You already know the goal from the conversation so far. Take it as far as you
can without further input:

1. **Make your own decisions.** When you hit a fork (which fix shape, which
   library, naming, edge-case handling, how to structure a test), pick the most
   reasonable option and proceed. Don't stop to ask "do you want A or B?" —
   choose, note why, and keep going. Andrew can course-correct later.
2. **Do NOT ask questions.** Andrew is away and will not answer. If you're
   genuinely blocked, exhaust every avenue yourself (read the code, check
   `.envrc` / project config for creds, `direnv allow`, re-run) before treating
   it as blocked. Being blocked on auth is never the answer.
3. **Fix and ship — don't file and stop.** If you discover a real bug or gap
   that blocks the mission, fix it and ship the fix. Only fall back to filing a
   tracking issue if the work is genuinely out of scope for this session.
4. **Drive it through `/shipit`.** Once the work is implemented, run the full
   ship workflow: test → test-review → docs-review → coderabbit → version bump →
   PR → merge → wait for deploy → verify health → test the new functionality.
   Skip steps already done. If a project has no `/shipit`, run the equivalent:
   test, review, PR, merge, and verify.
5. **Verify, review, iterate.** After shipping, actually confirm the change
   works (real end-to-end where it matters, not just unit tests). If
   verification surfaces a new problem, loop back and fix it. Use as many
   `/shipit` iterations as needed.

## Hard limits (these still apply — autonomy is bounded by them)

- **Respect the project's release boundary.** If the project follows a
  dev-first / staged release flow, the terminal state for a Claude session is
  "merged to the integration branch + that deploy verified" — do NOT cut prod
  releases or merge release PRs to the production branch unless the project's
  own conventions explicitly authorize a session to do so. When in doubt, ship
  to the integration branch, verify, and leave the prod release for Andrew.
- **Worktree safety.** Work in the worktree, never edit the main/read-only
  clones. Use `/start` to create an isolated worktree before product-repo work.
- **Follow the repo's PR / close-keyword conventions** (see the project's
  `CLAUDE.md` and docs).
- **Don't rotate shared demo/test credentials** unless that's the explicit task.
- **Honor any project-specific rules in `CLAUDE.md`** — those override this
  command where they conflict.

## When you're done (or truly blocked)

Stop and write a concise summary for when Andrew gets back:

- **What you did** — features shipped, PRs opened/merged, deploys verified.
- **Decisions you made** — the forks you hit and which way you went, so Andrew
  can quickly spot anything he'd have chosen differently.
- **What's left or blocked** — anything you couldn't finish and why.

Then stop cleanly. Thank you — go.
