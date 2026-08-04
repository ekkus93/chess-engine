---
description: Run the repository's Rust fast validation workflow. Use only when the user explicitly invokes this skill.
allowed-tools:
  - Bash(bash scripts/dev.sh fast)
---

# Lint and test

Run the authoritative fast Rust gate:

```bash
bash scripts/dev.sh fast
```

Stop at the first failure and report the exact command and diagnostic. Do not substitute Python lint/test commands; Python development and Python CI are retired.
