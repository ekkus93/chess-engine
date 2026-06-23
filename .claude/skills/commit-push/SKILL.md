---
description: Stage changed files, create a commit, and push to GitHub. Use only when the user explicitly invokes this skill.
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

# Commit and Push

Stage the appropriate files, commit, and push to GitHub. Use only when explicitly invoked.

## Steps

### 1. Inspect state

```bash
git status --short
git branch --show-current
git diff --stat
git diff HEAD
```

If there is nothing to commit, say so and stop.

### 2. Safety checks

Stop and ask the user what to do if any of the following are present:

- Secrets, API keys, passwords, tokens, or `.env` contents.
- Large generated files, build artifacts, or binary blobs that look accidental.
- Broken conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
- Changes that look incomplete or unrelated to each other.
- A detached HEAD or a branch with no configured upstream.

### 3. Commit

Write a concise conventional-style commit message (subject under 72 characters). Use a prefix when it fits: `fix:`, `feat:`, `docs:`, `test:`, `refactor:`, `chore:`, `build:`, `ci:`.

Stage only files that belong to the change, then commit:

```bash
git add <files>
git commit -m "<message>"
```

**Never add a `Co-Authored-By:` line** — a commit-msg hook rejects it.

Do not use `--no-verify`.

If the commit fails, report the error and stop.

### 4. Push

```bash
git push
```

If the branch has no upstream, stop and report the branch name. Do not guess the remote.

## Output

After pushing, report: commit hash, commit message, branch, and push result.

$ARGUMENTS
