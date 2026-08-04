---
description: Commit validated repository changes directly to master and push. Use only when the user explicitly invokes this skill.
model: haiku
effort: low
allowed-tools:
  - Bash(git status *)
  - Bash(git diff *)
  - Bash(git add *)
  - Bash(git commit *)
  - Bash(git push *)
  - Bash(git branch *)
  - Bash(git log *)
---

# Commit and push

This repository's standing policy is direct work on `master`. Do not create a branch or pull request unless the user explicitly requests one.

1. Verify `git branch --show-current` is `master`; otherwise stop.
2. Inspect `git status --short`, `git diff --stat`, and `git diff HEAD`.
3. Reject secrets, conflict markers, unrelated changes, transient generated output, or incomplete work.
4. Run the validation appropriate to the task; for normal Rust work use `bash scripts/dev.sh fast`.
5. Stage only task-related files and commit with a concise conventional subject. Never add a co-author trailer and never bypass hooks.
6. Push `master` normally. Do not force-push `master`.
7. Report exact commit SHA and validation evidence.
