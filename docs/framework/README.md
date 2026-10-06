# ADE - Agentic Development Environment (Cursor)

A small, reusable engineering framework on top of Cursor. You give a **goal**; the orchestrator routes it through only the
roles it needs, with human approval on anything risky. It is built from Cursor-native pieces plus a few stdlib-only Python scripts.

```
GOAL -> UNDERSTAND -> PLAN -> RESEARCH -> ARCHITECT -> IMPLEMENT -> TEST -> REVIEW -> SECURITY -> OPTIMIZE -> RELEASE -> OBSERVE
```

## How it works

| Piece | Where | What it does |
|---|---|---|
| Rules (policy, always-on or by file glob) | `.cursor/rules/*.mdc` | Principles, architecture + Definition of Done, security, git, docs, database, ponytail, interaction log |
| Skills (procedures) | `.cursor/skills/*/SKILL.md` | One reusable workflow per role, plus `orchestrator` (router) and `ponytail-review` |
| Subagents (isolated specialists) | `.cursor/agents/*.md` | Fresh context for research, independent review, security, profiling, etc. |
| Hooks (mechanical enforcement) | `.cursor/hooks.json`, `~/.cursor/hooks.json` | `guard.py` (approval on risky shell commands), `log_interaction.py` (query/response log, including empty Cursor windows) |
| Verification | `scripts/ade/verify.py` | Detects real build/lint/type/test commands, secret scan, TEST REPORT |
| Entry point | `scripts/ade/goal.ps1` | Starts Cursor Agent CLI with the orchestrator prompt (optional) |
| CI | `.github/workflows/ci.yml` | Same verification on PR/push; deploy is a disabled placeholder |
| Spec-driven work | `.cursor/skills/speckit-*`, `.specify/` | GitHub Spec Kit, unmodified |

## Use it

### Start a new project

1. Fill `PROJECT.md` (sections 1-6 minimum).
2. Run `pwsh scripts/ade/kickoff.ps1` (add `-Fix` to install the user-hook fallback and scrub legacy audit).
3. In Cursor chat: `Use the orchestrator skill for the goal in PROJECT.md`.
   From a terminal: `./scripts/ade/goal.ps1 "<goal>" [-Plan]`.
4. Spec-driven feature: `/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement` (constitution: `.specify/memory/constitution.md`).

### Day-to-day

In Cursor chat just state the goal ("Implementa OAuth", "Corrige este typo"); the always-on rules tell the agent to use the
`orchestrator` skill for non-trivial work. Verification only: `python scripts/ade/verify.py` (`--list`, `--json`, `--timeout N`, `--no-secrets`).
Tooling tests: `python -m unittest discover -s tests`.

## Mandatory interaction log

Every user query and assistant response is appended to `docs/framework/log/YYYY-MM-DD.md` by two hooks
(`beforeSubmitPrompt`, `afterAgentResponse`) running `scripts/ade/log_interaction.py`. Project hooks cover an opened
repository. The installed user-level fallback covers this repository's conversations in a Cursor empty window, but is
scoped by an exact Cursor transcript-path component and does not capture other projects or duplicate project hooks.
For privacy, the project log records only the event's role and character count: prompt/response
content remains in Cursor's own transcript and is never copied into this repository. The log is **local and git-ignored by
default** (remove the line in `.gitignore` to version it).
Manage the fallback with `python scripts/ade/install_cursor_hooks.py --show|--install-user|--uninstall-user`.
The rule is `.cursor/rules/interaction-log.mdc`; fallback:
`python scripts/ade/log_interaction.py --manual --user-chars <N> --assistant-chars <N>` (metadata only).

## Ponytail (anti-over-engineering)

Official [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) v4.10.0: always-on rule `.cursor/rules/ponytail.mdc`
(verbatim upstream) + skill `ponytail-review`. Details in [ARCHITECTURE.md](ARCHITECTURE.md#ponytail-integration).

## Documents

[ARCHITECTURE](ARCHITECTURE.md) - [WORKFLOW](WORKFLOW.md) - [AGENTS](AGENTS.md) - [SKILLS](SKILLS.md) -
[GOVERNANCE](GOVERNANCE.md) - [REPOSITORY_ANALYSIS](REPOSITORY_ANALYSIS.md) - [VALIDATION](VALIDATION.md) - [adr/](adr/0000-template.md)

## Extending

- New role: `.cursor/skills/<name>/SKILL.md` (frontmatter `name` = directory, `description` decides when it triggers), optionally
  `.cursor/agents/<name>.md`, a row in the orchestrator route table, and a row in [SKILLS.md](SKILLS.md)/[AGENTS.md](AGENTS.md).
- New stack: extend `detect()` in `scripts/ade/verify.py` (+ test) and a CI setup step.
- New guard rule: append to `RULES` in `scripts/ade/guard.py` (+ test).
- `python -m unittest discover -s tests` checks structure (frontmatter, names, hooks, referenced paths), so drift fails fast.
- Framework changes proposed by the agent (new rules/skills/scripts) need human approval; core rules never change silently.

## Limitations

See [ARCHITECTURE.md](ARCHITECTURE.md#what-is-real-and-what-is-not).
