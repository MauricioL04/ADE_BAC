---
name: architecture
description: Architectural review and decisions - boundaries, coupling, circular dependencies, new abstractions, schema changes, breaking changes, scalability, maintainability - and ADRs. Use for new features that add modules/dependencies, refactors, schema or API contract changes. Read-only except ADRs.
---

# Architecture

Goal: the simplest structure that meets the requirements. No architecture without a stated reason (see `ponytail.mdc`).

## Procedure

1. Read the plan and the affected modules; map current boundaries and dependency direction (FACT, from code).
2. Detect and list: boundary changes; coupling increases; circular dependencies; new abstractions (does a second
   implementation exist today?); schema changes; breaking changes (API, config, data format); scalability limits; maintainability cost.
3. For each real decision, give 2-3 options with trade-offs and pick one; prefer the option that adds the fewest files, layers and dependencies.
4. If the decision is important (hard to reverse, cross-cutting, new dependency, schema/contract change), write an ADR:
   copy `docs/framework/adr/0000-template.md`, next sequential number, fields Context / Decision / Alternatives / Consequences / Status.
5. High-impact decisions require HUMAN APPROVAL before implementation.

## Output

```
# ARCHITECTURE REVIEW
## Decision(s)   each: options -> chosen -> why (FACT / INFERENCE / ASSUMPTION)
## Impact        boundaries, coupling, cycles, schema, breaking changes, scalability
## Simplicity check   what was deliberately NOT added
## ADR           path or "not needed"
## Approval      required? (yes/no + reason)
```
