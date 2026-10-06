---
name: code-review
description: Code review of the current changes WITHOUT modifying files. Finds bugs, concurrency issues, error handling gaps, performance, maintainability, breaking changes and insufficient tests. Use after tests pass.
---

# Code review

**Phase 1 is read-only. Do not edit, create or delete files, and do not run anything that changes state.**
Review the diff (`git diff`, `git status`, plus untracked files) and the surrounding code. Prefer running as a separate
subagent (Task, readonly) so the review is independent of the author's context.

## Check

Bugs and incorrect logic; race conditions and concurrency; error handling; performance; maintainability; duplicated code;
unnecessary complexity; API compatibility and breaking changes; logging (present, no sensitive data); insufficient or
weak tests (do they fail if the code is wrong?); architectural problems and violations of `.cursor/rules/*`; scope creep
(unrelated changes); over-engineering (run the `ponytail-review` skill on the diff and list its findings as Low/Medium;
it never overrides security, validation, error handling or necessary tests).

Only report issues you can point to (file:line and why). No speculative nitpicks; no invented problems.

## Output format

```
# CODE REVIEW

## Critical      (must fix; correctness/data loss/security)
## High
## Medium
## Low
## Positive Findings
## Recommendation   (APPROVE / APPROVE WITH CHANGES / REJECT + reason)
```

Each finding: `[ID] file:line - problem - why it matters - suggested fix`.

## After the review

The orchestrator sends CRITICAL/HIGH findings to `coder`. You do not fix them yourself. On re-review, verify each
previous finding is resolved and that the fix introduced no new issue.
