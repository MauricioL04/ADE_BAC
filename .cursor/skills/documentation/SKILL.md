---
name: documentation
description: Updates documentation so it reflects reality - README, framework docs, API/config docs, .env.example, ADRs - only where the change requires it. Use at the end of a feature/behavior/config change. Never documents unimplemented features.
---

# Documentation

Docs describe what exists. Future work is labelled "Planned". Do not create documentation nobody needs.

## Procedure

1. From the diff, list user-visible or contract changes: behavior, setup, commands, config/env vars, API, architecture.
2. Update only the affected docs: `README.md` (if present), `docs/framework/*.md` when the ADE itself changes, API/config docs, `.env.example` (no real values).
3. Architectural decisions -> ADR in `docs/framework/adr/` (template `0000-template.md`, next number).
4. Verify every command, path and option you write by checking it exists or running it. Remove statements that are no longer true.
5. Do not duplicate: link to the source of truth instead of copying it.

The interaction log (`docs/framework/log/`) is written by hooks; do not hand-edit it.

## Output

`Docs updated: <files> - <what changed>` or `Docs: N/A - <reason>`.
