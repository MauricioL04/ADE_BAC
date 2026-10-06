# ADE architecture

## Principle

Goal-centric development on Cursor. The **orchestrator** classifies the goal and runs only the needed roles, with explicit
gates. Policy lives in **rules**, procedures in **skills**, isolated specialists in **subagents**, hard enforcement in
**hooks/scripts/CI**. There is no custom agent runtime.

```
                 HUMAN
                   |
                  GOAL
                   v
             ORCHESTRATOR  (skill)  -- picks the lightest safe route
   +-------+-------+-------+-------+-------+
   v       v       v       v       v       v
RESEARCH PLANNER ARCHITECT CODER  DEBUGGER  DATABASE / PERFORMANCE
   +-------+-------+-------+-------+-------+
                   v
              TESTER  ---- scripts/ade/verify.py
                   v
        REVIEWER / SECURITY  (independent, read-only subagents)
                   v
            PONYTAIL PASS  (transversal: what can we delete?)
                   v
            DOCS -> RELEASE (human approval) -> OBSERVE
```

## Skills vs subagents vs rules

| Mechanism | Use for | Here |
|---|---|---|
| Rule | Permanent principles, restrictions, conventions | `core-principles`, `architecture`, `coding-standards`, `testing`, `security`, `git`, `documentation`, `database`, `ponytail`, `interaction-log` |
| Skill | Multi-step reusable procedure, runs in the main context | one per role + `orchestrator` + `ponytail-review` |
| Subagent | Isolated work: research, independent review, specialists, parallel tasks | `.cursor/agents/*.md` (see [AGENTS.md](AGENTS.md)) |
| Orchestrator | Deciding which combination to use | `.cursor/skills/orchestrator/SKILL.md` |

The skill is the procedure (single source of truth); the subagent file is a thin wrapper that gives that procedure an
isolated context, permissions (`readonly`) and a compact output contract.

## Speed and context management

- Route by size: a typo runs coder -> tester, not the whole pipeline.
- Each subagent receives only goal, needed context, relevant files, prior results and constraints, and returns a compact
  structured result (the format defined in its skill). The conversation is not forwarded wholesale.
- Independent work is parallelized (research questions; reviewer + security after tests pass).
- Rules that always apply are short; longer guidance sits in skills that load only when relevant.

## Ponytail integration

Source inspected: `github.com/DietrichGebert/ponytail` @ `e3ba2aa` (v4.10.0, 2026-09-14). It ships native Cursor support in two
alternative forms: (a) `.cursor/rules/ponytail.mdc` (always-on rule) and (b) `hooks.json` session hooks (installer `cursor-hooks.js` in the upstream repo;
upstream's own cursor-hooks doc states that rule and hooks are alternatives, not layers).

| Decision | Reason |
|---|---|
| Installed the **rule** verbatim: `.cursor/rules/ponytail.mdc` | Official Cursor form, `alwaysApply: true`, no runtime dependency |
| Installed skill `ponytail-review` verbatim | Used by the transversal "what can we delete" pass; loaded natively by Cursor |
| Did **not** install hooks | Excluded by upstream when the rule exists; needs Node; ~1 s per prompt on Windows (upstream measurement) |
| Did **not** copy `ponytail`, `-audit`, `-debt`, `-gain`, `-help` skills | Rule already provides the behavior; avoids duplicate instructions and context cost. Add later by copying from upstream if wanted |
| Project policy kept **separate** | Vendor files are unmodified. Project-specific limits (never remove security/validation/tests) live in `core-principles.mdc`, `orchestrator`, `code-review`, `reviewer` |

Where it acts: `coder`/`planner` (ladder before writing code), `reviewer` (ponytail-review on the diff), orchestrator (gate before approval).
Not verified: whether subagents inherit always-on rules (upstream only documents that its *hook* ruleset never reaches subagents), so the `coder` and `reviewer` subagent files reference ponytail explicitly.

**Update procedure**: fetch upstream, diff `.cursor/rules/ponytail.mdc` and `skills/ponytail-review/SKILL.md` against the installed copies, review the
diff (they are prompt content loaded into every session), copy, and update the commit above.

## Components (all real files)

| Layer | Files |
|---|---|
| Policy | `.cursor/rules/*.mdc` |
| Roles | `.cursor/skills/*/SKILL.md`, `.cursor/agents/*.md` |
| Enforcement | Project `.cursor/hooks.json` -> `scripts/ade/guard.py`, `scripts/ade/log_interaction.py`; user fallback managed by `scripts/ade/install_cursor_hooks.py` |
| Verification | `scripts/ade/verify.py` -> `.ade/runs.jsonl` (local, git-ignored) |
| Structure checks | `tests/test_framework.py`, `tests/test_ade_tools.py` |
| CI | `.github/workflows/ci.yml` |
| Knowledge | `docs/framework/*.md`, `docs/framework/adr/`, `docs/framework/log/` |

## Observability (prepared, minimal)

Today: `verify.py` run log; interaction log. Planned when a deployable service exists (deliberately not built): structured logs,
OpenTelemetry metrics/tracing, `/health` contract consumed by `release`, alerts on health checks, incident analysis via the `debugging` skill.

## What is real and what is not

- **Real, mechanical**: `guard.py` approval hook, `log_interaction.py` hooks (including the installed empty-window fallback), `verify.py`, CI workflow (untested until pushed), structure tests.
- **Behavioral (model-followed)**: routing, role separation, gates, Definition of Done, ponytail. Skills and rules are instructions, not sandboxes.
- **Depends on Cursor**: rule/skill loading, hooks execution, subagents (Task tool) and their `readonly` enforcement.
- **Depends on external tools**: Python 3, Git; Cursor Agent CLI for `goal.ps1`; project-specific toolchains detected by `verify.py`.
- **Not built (Planned)**: language toolchains (no app code yet), observability stack, deploy job, performance profilers, DB connectivity.
- **Known hard limit**: a Cursor conversation with neither a workspace root nor a transcript path cannot be safely attributed to this repo; the user-level fallback intentionally skips it rather than logging another project's conversation here.
