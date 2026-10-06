# ADE project constitution

This constitution binds Spec Kit workflows (`/speckit-*`) to the ADE framework rules. It does not restate
those rules; it points to them. When a Spec Kit template asks for a principle, use the ones below.

## Core principles (source of truth)

- Engineering principles: `.cursor/rules/core-principles.mdc` (understand-before-code, plan-before-large-changes,
  reuse-before-reinvent, simple solutions, verify-not-assume, separated review, security-first, tests-as-evidence,
  measured performance, human approval for irreversible/high-impact actions, docs reflect reality, minimize code,
  preserve conventions, never invent APIs/dependencies/behavior, never claim without verification).
- Architecture and DoD: `.cursor/rules/architecture.mdc`.
- Anti-over-engineering (Ponytail): `.cursor/rules/ponytail.mdc`. YAGNI, stdlib first, one line if possible; never
  at the cost of validation, security, error handling, needed tests, accessibility or requirements.
- Security baseline (AppSec, secrets, database safety): `.cursor/rules/security.mdc`, `.cursor/rules/database.mdc`.
- Testing: `.cursor/rules/testing.mdc` (real project commands only; SKIP is not PASS; bug fix = failing regression test first).
- Git: `.cursor/rules/git.mdc` (no push to main/master, no force push, no `--no-verify`, no secrets).
- Documentation: `.cursor/rules/documentation.mdc` (only what exists; ADRs for real decisions).
- Mandatory interaction audit: `.cursor/rules/interaction-log.mdc` (metadata-only, git-ignored).

## Additional constraints (this project)

- Stack, runtime and integrations: **TBD**. Set in `PROJECT.md` before implementation; the researcher confirms with FACT/INFERENCE/ASSUMPTION.
- No dependency, abstraction, file, layer or config that a smaller solution does not need.
- Third-party prompt content (rules/skills loaded into every session) is reviewed before install and again on upgrade.

## Workflow gates

- Route selection: `.cursor/skills/orchestrator/SKILL.md`.
- Plan approval gate: > ~10 files, refactor, schema/migration, new dependency, architecture change, or anything destructive.
- Test gate: `python scripts/ade/verify.py` PASS on every applicable stage.
- Independent review: `code-review` and `security` run as subagents (`.cursor/agents/{reviewer,security}.md`), read-only.
- Ponytail pass: `.cursor/skills/ponytail-review/SKILL.md` before approval; only proposes deletions/shrinks.
- Release: `release` skill; production requires explicit human approval and a rollback plan.

## Governance

- This constitution supersedes ad-hoc practices; the rules it points to are the source of truth. Amend by editing
  those rules and then this file, with an ADR in `docs/framework/adr/` (template `0000-template.md`).
- Changes to `core-principles.mdc`, `security.mdc`, `git.mdc`, `interaction-log.mdc`, hooks and approval gates
  require explicit human approval.

**Version**: 1.0.0 | **Ratified**: 2026-09-29 | **Last Amended**: 2026-09-29
