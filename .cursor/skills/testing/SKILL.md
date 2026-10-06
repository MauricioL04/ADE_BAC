---
name: testing
description: Validates a change - builds, creates and runs tests, checks regressions, lint and type checking, and produces a TEST REPORT. Use after implementation and before review, or before deployment.
---

# Testing

## A change is NOT complete if

it does not compile/build, does not run, any test fails, there are regressions, lint fails, or type checking fails (when a type checker exists).

## Procedure

1. Discover the real commands: `python scripts/ade/verify.py --list`. Cross-check with manifests, README and CI. Never invent commands. If a stage has no command, it is SKIP (not applicable) and you say so.
2. Create tests for new functionality (in `tests/` or the stack's convention): happy path, edge cases, error paths.
3. Run existing tests, then the new ones, then the whole suite for regressions.
4. Run lint and the type checker if they exist.
5. Run the mechanical gate: `python scripts/ade/verify.py` (build, lint, type check, tests, secret scan; appends to `.ade/runs.jsonl`).
6. On failure: report the error, diagnose the cause, propose (or with permission apply) the fix, then RE-RUN all validations - not only the failing one.
7. Repeat until PASS or escalate after 3 failed attempts with the diagnosis.

## Output format

```
TEST REPORT

Build:
PASS / FAIL

Unit Tests:
PASS / FAIL

Integration Tests:
PASS / FAIL

Regression:
PASS / FAIL

Lint:
PASS / FAIL

Type Check:
PASS / FAIL

Remaining Issues:
```

Use `N/A` or `SKIP (reason)` where no command exists; never write PASS for something that did not run.
Include the exact commands executed and their outcome.
