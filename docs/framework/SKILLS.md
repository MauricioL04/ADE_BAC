# Skills

Files: `.cursor/skills/<name>/SKILL.md`. The `description` decides when Cursor loads a skill.

| Skill | Purpose | Key contract |
|---|---|---|
| `orchestrator` | Classify the goal, choose the route, enforce gates and DoD | route table; skill vs subagent; loop limits |
| `planner` | Executable plan before non-trivial change (read-only) | PLAN: Goal, Current State, Requirements, Constraints, Files, Implementation, Architecture impact, Dependencies, Testing, Security, Risks, Rollback, Acceptance; high impact => human approval |
| `researcher` | Remove technical uncertainty, repo first, official docs | FACT / INFERENCE / ASSUMPTION |
| `architecture` | Boundaries, coupling, cycles, schema/breaking changes, ADRs | ARCHITECTURE REVIEW; simplest option wins |
| `testing` | Discover real commands, write/run tests, TEST REPORT | never invent commands; SKIP is not PASS |
| `code-review` | Independent review, no edits | CRITICAL / HIGH / MEDIUM / LOW; includes ponytail pass |
| `security` | AppSec review | CONFIRMED / POTENTIAL / FALSE POSITIVE; no invented vulns |
| `debugging` | Root cause analysis | SYMPTOM -> REPRODUCE -> TRACE -> ISOLATE -> ROOT CAUSE -> FIX -> REGRESSION TEST |
| `database` | SQL/schema/migrations/locks, Oracle-aware | destructive: ANALYZE -> SCRIPT -> IMPACT -> APPROVAL -> EXECUTE |
| `performance` | Measurement-driven optimization | BASELINE -> MEASURE -> PROFILE -> CHANGE -> BENCHMARK -> COMPARE |
| `documentation` | Keep docs true, ADRs | only what the change affects; verify commands |
| `release` | Build, staging, health checks, rollback, observability readiness | stops at HUMAN APPROVAL; never auto-deploys production |
| `ponytail-review` | Over-engineering review (upstream, verbatim) | one line per finding, `net: -N lines possible`; out of scope: bugs/security/perf |
| `speckit-*` | Spec Kit (spec -> plan -> tasks -> implement) | unmodified upstream |

Rules (always-on unless noted): `core-principles`, `architecture`, `security`, `git`, `documentation`, `ponytail`, `interaction-log`;
by context: `coding-standards`, `testing`, `database` (SQL/migration globs).
