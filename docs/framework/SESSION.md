# Session handoff

Read this first when resuming. It is short on purpose. Update it at the end of every working session.

## Where we are

**State**: framework ready to accept a project brief. No application code exists yet.
**Waiting on**: the user to fill `PROJECT.md` with the real case (goal, users, scope, constraints, acceptance).
**Last verified**: 2026-09-29 — 38 tests PASS, `verify.py` PASS on applicable stages, `kickoff.ps1` 4/4 PASS.

## What exists (do not rebuild)

- `.cursor/rules/*.mdc` — 10 always-on rules (core principles, architecture, coding, testing, security, git, docs, database, ponytail, interaction-log).
- `.cursor/skills/*/SKILL.md` — 13 skills (orchestrator, planner, researcher, architecture, testing, code-review, security, debugging, database, performance, documentation, release, ponytail-review) + Spec Kit skills.
- `.cursor/agents/*.md` — 10 subagents (explorer, architect, coder, tester, reviewer, security, debugger, database, performance, release). Read-only: explorer, architect, reviewer, security, database.
- `.cursor/hooks.json` — project hooks: `guard.py` on shell, `log_interaction.py` on prompt/response.
- `~/.cursor/hooks.json` — user-level fallback installed by `scripts/ade/install_cursor_hooks.py`, scoped by transcript path so it only fires for this project.
- `scripts/ade/{verify,guard,log_interaction,install_cursor_hooks,kickoff}.py|ps1`, `scripts/ade/goal.ps1` — all Python 3 stdlib.
- `tests/` — 38 tests (`test_framework.py`, `test_ade_tools.py`).
- `docs/framework/` — README, ARCHITECTURE, WORKFLOW, AGENTS, SKILLS, GOVERNANCE, REPOSITORY_ANALYSIS, VALIDATION, this SESSION.md, and `adr/0001`, `adr/0002`.
- `.specify/` — Spec Kit installed unmodified; `.specify/memory/constitution.md` binds `/speckit-*` to the framework rules.
- `PROJECT.md` — empty intake form at repo root.

## What is intentionally missing (Ponytail: do not add until asked)

- No `src/`, `app/`, package manifest, Dockerfile, framework, ORM, linter/type-checker config.
- No stack choice, no runtime, no DB, no deploy target.
- No new dependency beyond Python stdlib + Spec Kit's `specify-cli` (already installed) + Ponytail rule content (already vendored).

## Resume in 60 seconds

```powershell
pwsh scripts/ade/kickoff.ps1        # must show 4/4 PASS
Get-Content PROJECT.md              # is section 1 (Goal) still TBD?
```

- If `PROJECT.md` is still empty: ask Mauricio to fill sections 1-6, then route the goal through the `orchestrator` skill.
- If `PROJECT.md` is filled: read it, then say `Use the orchestrator skill for the goal in PROJECT.md`. The orchestrator classifies the route (planner-only, or full ARCHITECT->IMPLEMENT->TEST->REVIEW->SECURITY->RELEASE, or Spec Kit).
- If any check in `kickoff.ps1` fails: run `pwsh scripts/ade/kickoff.ps1 -Fix` first (reinstalls user hooks, scrubs legacy audit files); if it still fails, investigate before touching the case.

## Ground rules for the next agent (Mauricio's non-negotiables)

- **Cycle**: ANALIZA -> DISEÑA -> IMPLEMENTA -> VALIDA -> DOCUMENTA. Never skip ANALIZA.
- **Never invent** APIs, dependencies, commands, config or behavior. FACT / INFERENCE / ASSUMPTION labels when reporting.
- **Never claim done** without running `python scripts/ade/verify.py` and reporting the DoD table.
- **Human approval** before: production, destructive ops, mass changes (~>10 files), secret/permission changes, schema/data migrations, force pushes, `--no-verify`.
- **Interaction audit** is mandatory (`.cursor/rules/interaction-log.mdc`) and metadata-only by design; do not add message bodies.

## Key decisions already made (do not relitigate)

- ADR-0001: ADE built on Cursor native primitives only (rules, skills, subagents, hooks). No custom runtime.
- ADR-0002: Ponytail integrated as a rule (not hooks) + `ponytail-review` skill; interaction log is metadata-only.
- Constitution (`.specify/memory/constitution.md`) points at the rules rather than restating them. Amendments require an ADR.
- `PROJECT.md` is the single intake surface for the case. `scripts/ade/kickoff.ps1` is the single health-check entry point.

## Pending / open items

- (none at framework level) Waiting for the case to be placed.
- CI (`.github/workflows/ci.yml`) has never run against a remote; will validate on first push.
- Stack-specific verification stages (Lint, Type check, Integration) currently SKIP; the `detect` step inside `scripts/ade/verify.py` picks up Node/Python/Go/Rust manifests automatically when they appear.

## Housekeeping

At the end of every session update: **Where we are**, **Last verified**, **Pending / open items**. Keep the rest stable.
