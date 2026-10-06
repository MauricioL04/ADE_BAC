# ADE workflow

## Start a project

1. Fill `PROJECT.md` (goal, users, scope, constraints, acceptance criteria).
2. `pwsh scripts/ade/kickoff.ps1` — health check (tests, verify, hook status, brief present). Add `-Fix` to also install the user-hook fallback and scrub legacy audit files.
3. Read `.specify/memory/constitution.md`; it binds Spec Kit to the framework rules.
4. In Cursor chat: `Use the orchestrator skill for the goal in PROJECT.md`. The orchestrator classifies and picks a route.
5. Feature-sized work? Run `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`. The planner may summarize instead when a spec is overkill.

## Run a goal

Cursor chat: state the goal (the rules route non-trivial work to the `orchestrator` skill). Terminal:

```powershell
./scripts/ade/goal.ps1 "Implementa autenticacion OAuth"          # interactive; approvals stay on
./scripts/ade/goal.ps1 "Implementa autenticacion OAuth" -Plan    # planning first (read-only plan mode)
```

## Routes (only what the goal needs)

| Request | Route |
|---|---|
| "Corrige este typo" | coder -> tester |
| "Implementa OAuth" | researcher -> planner -> architect -> coder -> tester -> security -> reviewer (+ ponytail pass, docs) |
| "Optimiza esta query Oracle" | database -> performance -> tester -> reviewer |
| "Investiga por que el endpoint esta lento" | researcher -> performance -> debugger |
| "Prepara produccion" | tester -> security -> reviewer -> release -> **HUMAN APPROVAL** |
| Bug with unknown cause | debugger -> coder (regression test first) -> tester -> reviewer |

## Gates

Plan approval (large/risky) - test gate - review loop (max 3, then human) - security gate (CONFIRMED blocks) - ponytail pass -
docs - Definition of Done - human approval for release. Details: [GOVERNANCE.md](GOVERNANCE.md).

## Example - "Implementa OAuth"

1. **Researcher** (subagents in parallel: provider docs / existing auth code / dependencies): FACT / INFERENCE / ASSUMPTION list.
2. **Planner**: PLAN (files, new dependency, risks: token storage, redirect URI, rollback). New dependency => *awaiting human approval*.
3. **Architect**: where auth lives, boundary with sessions; ADR for the library choice.
4. **Coder**: secrets only via env vars + `.env.example`; tests for state/nonce validation and failure paths.
5. **Tester**: TEST REPORT, re-run fully after each fix.
6. **Security** and **Reviewer** (independent read-only subagents, in parallel): e.g. HIGH missing `state` check -> back to coder.
7. **Ponytail pass**: `ponytail-review` on the diff (unneeded wrapper, one-implementation interface) -> delete; never the `state` check.
8. **Docs** + Definition of Done report.

## Example - "Optimiza esta query Oracle"

**Database**: confirm Oracle version (FACT or ASSUMPTION), request the real plan (`DBMS_XPLAN`); find non-sargable predicates, missing
index, literals instead of binds; SQL proposals marked NOT EXECUTED. **Performance**: baseline -> change -> benchmark -> compare.
Index/DDL is delivered as a script with impact; running it needs human approval. **Tester**: equivalence tests. **Reviewer**.

## Example - "Prepara produccion"

Tester -> Security -> Reviewer -> Release (build, config vs `.env.example`, migrations reviewed by `database`, changes, rollback,
health checks) -> "AWAITING HUMAN APPROVAL". Deploy only after explicit approval, then health check.

## Validation run

A real end-to-end run of the framework on a small task is recorded in [VALIDATION.md](VALIDATION.md).
