# Subagents

Files: `.cursor/agents/<name>.md` (frontmatter: `name`, `description`, `model: inherit`, `readonly`). Cursor decides delegation from
`description`; the orchestrator can also launch them with the Task tool. Each is a thin wrapper over the matching skill.

| Subagent | Skill it follows | Writes? | Use when | Output |
|---|---|---|---|---|
| `explorer` | `researcher` | no | Repo/docs/API/dependency questions; parallelizable | RESEARCH (FACT/INFERENCE/ASSUMPTION) |
| `architect` | `architecture` | no | Boundaries, new abstractions/deps, schema/API changes | ARCHITECTURE REVIEW (+ ADR draft) |
| `coder` | (self-contained) | yes | Well-defined implementation | files changed, tests, gaps |
| `tester` | `testing` | tests | After implementation, before review/release | TEST REPORT |
| `reviewer` | `code-review` + `ponytail-review` | no | Independent review of the diff | CODE REVIEW (CRITICAL..LOW) |
| `security` | `security` | no | Auth/input/config changes, pre-release | SECURITY REVIEW (CONFIRMED/POTENTIAL/FALSE POSITIVE) |
| `debugger` | `debugging` | fix + test | Cause not yet proven | ROOT CAUSE ANALYSIS |
| `database` | `database` | no (proposes SQL) | SQL, schema, migrations, query tuning | DATABASE REVIEW |
| `performance` | `performance` | change + benchmark | Slowness, optimization | PERFORMANCE REPORT |
| `release` | `release` | no deploy without approval | Release prep, health checks, rollback | DEPLOYMENT PLAN |

The planner, orchestrator, documentation and ponytail-review are skills only (small, sequential, need the main context).
Read-only agents (`readonly: true`) cannot edit files or run state-changing commands; that is enforced by Cursor, not by this repo.
Hand-off rule: pass goal, needed context, relevant files, prior results and constraints only.
