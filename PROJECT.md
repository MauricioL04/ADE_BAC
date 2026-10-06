# Project brief

Fill this in before starting. It is the single input to `orchestrator`, `researcher`, `planner` and Spec Kit.
Do not add sections you do not need; leave `TBD` when unknown so the researcher can pick them up.

## 1. Goal (one sentence)

TBD

## 2. Users and their real problem

- Primary user: TBD
- Job they need to get done: TBD
- Today they solve it by: TBD
- Success looks like: TBD

## 3. Scope

### In scope (MVP)

- TBD

### Explicitly out of scope

- TBD

## 4. Constraints

- Stack preference (or "no preference"): TBD
- Runtime target (server, CLI, web, desktop, mobile, edge): TBD
- Data / integrations required: TBD
- Compliance / security (auth, PII, regulated data): TBD
- Deadline / budget: TBD

## 5. Acceptance criteria

Each criterion must be independently testable.

- [ ] TBD
- [ ] TBD

## 6. Non-negotiables

- Follow `.cursor/rules/core-principles.mdc`, `security.mdc`, `ponytail.mdc`, `interaction-log.mdc`.
- Human approval before production, destructive ops, mass changes, secrets/permissions, schema/data migrations.
- No new dependency, abstraction or file without a justified need.

## 7. Risks and unknowns (for the researcher)

- TBD

## 8. Rollback / kill switch

- TBD

---

### Kickoff

1. Fill sections 1-6 (7 and 8 can start empty; the researcher/planner will complete them).
2. Run `pwsh scripts/ade/kickoff.ps1` to verify the framework is healthy.
3. In Cursor chat, state: `Use the orchestrator skill for the goal in PROJECT.md`.
   Or from a terminal: `./scripts/ade/goal.ps1 "<your goal>"`.
4. For a spec-driven feature, use Spec Kit: `/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement`.
