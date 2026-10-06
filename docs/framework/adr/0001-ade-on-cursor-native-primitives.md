# ADR-0001: Build the ADE on Cursor-native primitives

## Context

We want a goal-centric workflow (plan, research, implement, test, review, security, delivery) on Cursor Agent CLI.
The repo was empty, so there was no stack to integrate with. Cursor supports rules (`.cursor/rules/*.mdc`), skills
(`.cursor/skills/*/SKILL.md`), hooks (`.cursor/hooks.json`) and a CLI (`agent`, with `--plan`, `-p`, `--workspace`).
Spec Kit was requested and installs skills for Cursor.

## Decision

- Implement roles as skills, policy as rules, enforcement as one `beforeShellExecution` hook, verification as a
  stdlib-only Python script (`verify.py`), and use Spec Kit for spec-driven feature work.
- No custom agent runtime, no external services, no new dependencies beyond Python's standard library.
- No automatic deployment; human approval gates everywhere risk exists.

## Alternatives

- Separate processes/agents per role (custom orchestrator with the Cursor SDK): more control, much more code to maintain, unnecessary now.
- Only prompts/rules, no scripts: no deterministic verification or enforcement.
- Bash/PowerShell-only scripts: less portable than Python across Windows and Linux CI.

## Consequences

+ Small, auditable, works in IDE and CLI, easy to extend (see `docs/framework/README.md`).
- Role separation is behavioral (model-followed), not sandboxed; hard guarantees come from the hook, CI and Cursor permissions.
- `verify.py` needs a new `detect()` branch for stacks other than Node/Python/Go/Rust.

## Status

Accepted
