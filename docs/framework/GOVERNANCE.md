# Governance

## Human approval gates (required before)

Production actions; destructive operations (data, files, git history); mass changes (> ~10 files or cross-cutting refactors);
high-impact architecture changes; destructive migrations / data loss; secret or permission changes; irreversible actions.
Plan gate: PLAN -> HUMAN APPROVAL -> IMPLEMENT for high-impact work. SQL: ANALYZE -> GENERATE SCRIPT -> SHOW IMPACT -> HUMAN APPROVAL -> EXECUTE.
Release: PREPARE -> VALIDATE -> SHOW CHANGES -> HUMAN APPROVAL -> DEPLOY.

## Enforcement levels

| Level | Mechanism | Strength |
|---|---|---|
| Hard | `guard.py` hook (`beforeShellExecution`) returns `ask` for force push, `reset --hard`, recursive delete, DROP/TRUNCATE/mass DELETE, deploy/publish commands, `.env` access, broad chmod, push to main/master | Pattern-based backstop; can miss obfuscated commands, variables/aliases and bare `git push` on main |
| Hard | CI (`verify.py`) on PR/push; secret scan | Runs only once pushed to GitHub |
| Hard | Interaction log hooks | Project hooks plus a user-level fallback scoped to this repo's empty-window transcript; failure never blocks the user |
| Cursor | `readonly` subagents; Cursor's own approval/permission settings | Enforced by Cursor |
| Behavioral | Rules and skills (routing, roles, gates, DoD) | Model-followed; verify with the reports, not trust |

## Security policy

Baseline in `.cursor/rules/security.mdc`: no secrets or personal data in files/logs/tests/docs/commits (env vars + `.env.example`); untrusted input;
server-side authz; least privilege; do not weaken TLS/CORS/auth/CSP to make something work; findings classified CONFIRMED / POTENTIAL /
FALSE POSITIVE with evidence. Third-party prompt content (e.g. Ponytail rule) is reviewed before install because it is loaded into every session.
The interaction audit persists only metadata (role and character count), not prompt or
response content. It is still git-ignored by default.

## Git policy

Small coherent commits; TEST -> REVIEW -> SECURITY -> DIFF REVIEW -> COMMIT before significant commits. Never: force push, `reset --hard`,
`clean -fd`, `branch -D`, `--no-verify`, overwrite unrelated/uncommitted work, commit secrets, change git config, push to main/master directly.
No commit/push/PR unless the user asks (`.cursor/rules/git.mdc`).

## Production policy

Production requires explicit human approval each time. Preconditions: tests PASS, review APPROVE, security PASS (or accepted conditions), a
rollback plan, and health checks. The CI `deploy` job is a disabled placeholder; no deploy command exists yet.

## Agent permissions

| Role | May edit code | May run state-changing commands | Notes |
|---|---|---|---|
| explorer, architect, reviewer, security, database | no (`readonly`) | no | report only; ADR text is written by the main agent |
| coder, debugger, performance | yes, within the approved plan | yes (guarded) | stop and ask for unplanned deps, destructive steps, secrets/permissions |
| tester | tests only | test/build commands | never invents commands |
| release | no | only after approval | deploys never automatic |

## Framework self-improvement

Agents may PROPOSE a rule, skill, subagent, script or automation with evidence. Changes to `core-principles.mdc`, `security.mdc`,
`git.mdc`, `interaction-log.mdc`, hooks, and approval gates require explicit human approval.

## Local Cursor configuration

`scripts/ade/install_cursor_hooks.py --install-user` installs the query/response and approval-guard fallback in
`~/.cursor/hooks.json`. It preserves unrelated hooks, is idempotent, uses a lock for updates, and adds entries only for
empty-window conversations whose Cursor transcript path contains this project's exact path marker. `--uninstall-user`
removes only those entries. This project has it installed to cover the observed Cursor empty-window condition.
