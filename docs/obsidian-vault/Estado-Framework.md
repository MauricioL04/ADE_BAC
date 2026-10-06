# Estado del Framework — ADE

> Snapshot: **2026-10-06**. Rama `master`, 6 commits iniciales.
> Fuente de verdad del inventario: el repo. Esta nota se actualiza cuando cambie la estructura.

## Validación

Ejecutado `python scripts/ade/verify.py`:

| Chequeo | Resultado |
|---|---|
| Unit tests (`tests/`) | PASS (39 tests) |
| Regression | PASS |
| Secret scan | PASS |
| Lint | SKIP (sin linter configurado todavía) |
| Type check | SKIP (sin type checker todavía) |
| Integration | SKIP (sin suite de integración todavía) |

Los SKIP son esperados: aún no hay stack de aplicación. Se activan cuando aparezca.

## Inventario

- **10 rules** en `.cursor/rules/` — core-principles, architecture, coding-standards, testing, security, git, documentation, database, ponytail, interaction-log.
- **23 skills propias** en `.cursor/skills/` — orchestrator, planner, researcher, architecture, testing, code-review, security, debugging, database, performance, documentation, release, ponytail-review y la familia `speckit-*` (10).
- **9 colecciones de skills externas** en `.cursor/skills/_external/` — **no versionadas** (`.gitignore`), instaladas en bulk el 2026-10-06. Ver [[Equipo]].
- **10 subagentes** en `.cursor/agents/` — explorer, architect, coder, tester, reviewer, security, debugger, database, performance, release.
- **16 docs** en `docs/framework/` — ARCHITECTURE, WORKFLOW, AGENTS, SKILLS, GOVERNANCE, REPOSITORY_ANALYSIS, SESSION, ADRs, plantillas.
- **Hooks** en `.cursor/hooks.json` — `guard.py` (beforeShellExecution), `log_interaction.py` (beforeSubmitPrompt + afterAgentResponse).
- **Spec Kit** en `.specify/` — templates, scripts PowerShell, constitution, workflows.
- **Scripts ADE** en `scripts/ade/` — verify, guard, log_interaction, install_cursor_hooks, helpers.
- **CI** en `.github/workflows/` — pipeline mínimo.

## Historial inicial (commits)

```
f6a6575 docs(vault): seed Obsidian investigation vault
12208d9 docs(framework): ADE framework documentation
84ca2ad feat(ade): tooling scripts, tests and CI workflow
f3fa450 feat(speckit): add Spec Kit integration (templates, scripts, memory)
1b846f9 feat(ade): add Cursor framework config (rules, skills, agents, hooks)
e88a8e0 chore: add gitignore and project overview
```

## Decisiones ya aplicadas

- **Skills de terceros ignoradas por git** (`.cursor/skills/_external/`): son ~670 archivos no auditados; se instalan localmente y no inflan diffs de PR. Para incluir una colección revisada, añadir una excepción explícita en `.gitignore` (`!.cursor/skills/_external/<nombre>/`).
- **Test `test_referenced_repo_paths_exist`** salta `_external/` para no romper por referencias de skills ajenas a sus propios instaladores.
- `.cache/` también excluida (artefactos de ejecución).

## Pendientes conocidos

- Ruido `Add-Content : No se puede leer la secuencia` en PowerShell: es del **wrapper del terminal de Cursor en Windows**, no de nuestros hooks. Verificado en aislamiento (los hooks devuelven JSON válido). Cosmético, no bloquea.
- Identidad git por defecto (`mauriciolinares@belcorp.biz`): si se quiere otra, ejecutar `git config user.name/email` y reescribir con `git commit --amend` o `git rebase -i --root`.
- Aún sin `remote origin`. No se ha hecho push (regla `git.mdc`).

## Enlaces

- [[Contexto]]
- [[Como-Trabajamos]]
- [[Equipo]]
- [[Plantilla-Proyecto-SRS]]
- Framework interno: `docs/framework/ARCHITECTURE.md`, `WORKFLOW.md`, `GOVERNANCE.md`.
