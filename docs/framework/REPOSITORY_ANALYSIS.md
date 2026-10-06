# Repository analysis

Updated 2026-09-29 (state: **ready to accept a project brief**).

## Findings

| Area | Finding |
|---|---|
| Application code | None. Only ADE tooling (Python 3 standard library): `scripts/ade/{verify,guard,log_interaction,install_cursor_hooks}.py`, `tests/`. |
| Project brief | `PROJECT.md` is present as an empty intake form; sections 1-6 must be filled before implementation. |
| Kickoff | `scripts/ade/kickoff.ps1` runs tests, verify, hook status and brief presence. Add `-Fix` to install the user-hook fallback and scrub legacy audit. |
| Stack / package manager | Python 3.14 + pip locally; no application manifests. `uv` was installed to fetch Spec Kit. |
| Testing | `unittest` in `tests/` (framework tooling + structure). 35 tests PASS. |
| Git | Local repo, no commits, no remote. Everything is untracked. |
| CI/CD | `.github/workflows/ci.yml` runs `verify.py` on PR/push; deploy is a disabled placeholder. Untested until pushed. |
| Docker / DB / env vars | None. Database rule and skill stay dormant until SQL/schema appears. |
| Cursor config | Project `.cursor/{rules,skills,agents,hooks.json}` in place. User-level `~/.cursor/hooks.json` has the ADE fallback installed, scoped by transcript path. |
| Spec Kit | `specify-cli` 1.0.14.dev0; `.cursor/skills/speckit-*` and `.specify/` present. Constitution now points to the framework rules. |
| Shell | Windows PowerShell 5.1: no heredoc; `Set-Content -Encoding UTF8` writes a BOM that breaks frontmatter (guarded by a test). |

## Reuse decisions

- Evolved the existing ADE instead of rebuilding: skills renamed to the target layout, `coder` moved to `.cursor/agents/`, docs moved under `docs/framework/`.
- Reused Cursor primitives only (rules, skills, subagents, hooks). No custom runtime, no new dependencies.
- Ponytail installed from upstream (rule + `ponytail-review`), see [ARCHITECTURE.md](ARCHITECTURE.md#ponytail-integration).
- Spec Kit constitution points at the framework rules rather than restating them.

## Implications

`verify.py` reports `SKIP` for stages without a command (no linter/type checker configured). When the project brief lands and code appears,
re-run the planner and update this file; `verify.py` will pick up Node/Python/Go/Rust manifests automatically, other stacks need a small
`detect()` extension in the same file.
