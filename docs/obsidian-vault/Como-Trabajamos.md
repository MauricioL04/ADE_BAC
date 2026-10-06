# Cómo trabajamos

## Flujo ADE (resumen operativo)

```
GOAL → UNDERSTAND → PLAN → RESEARCH → ARCHITECT → IMPLEMENT → TEST → REVIEW → SECURITY → OPTIMIZE → RELEASE → OBSERVE
```

Solo se corren las etapas que el goal necesita. Entrypoint: skill `orchestrator`
(`.cursor/skills/orchestrator/SKILL.md`). Para features con spec formal, Spec Kit: `/speckit-specify`, `/speckit-plan`,
`/speckit-tasks`, `/speckit-implement`.

Antes de modificar código no trivial: leer `docs/framework/SESSION.md` y `docs/framework/REPOSITORY_ANALYSIS.md`.

## Criterio de prioridad

El criterio se mide por **dificultad y esfuerzo esperado** de la tarea, no por urgencia percibida.

| Nivel | Señales | Ruta |
|---|---|---|
| **Trivial** | 1 archivo, cambio local, sin ambigüedad | Ejecutar directo + verificación mínima. No invocar orchestrator. |
| **Medio** | 2-10 archivos, lógica nueva, APIs internas conocidas | `planner` → `coder` → `tester` → `reviewer`. |
| **Alto** | Cambio arquitectónico, dependencia nueva, dato sensible, incertidumbre técnica | **`explorer` / `researcher` primero** (investiga, compara, saca lo mejor de las fuentes), luego `architect` → ADR → resto del pipeline. |
| **Destructivo / Producción** | Migraciones, borrado, deploy, cambios de permisos | STOP, pedir aprobación humana explícita. `guard.py` lo intercepta. |

Regla: **si no sabes cómo clasificarla, es Alto** → explorer primero.

## Reglas de tokens y contexto

### a) Compactación al 60%

- Al llegar al **60% del contexto**, se dispara `/clear` para liberar y compactar la conversación.
- `/clear` es un comando del **cliente Cursor**, no del repo → lo invoca Mauricio (o atajo del IDE). Yo señalo cuando convenga.
- Antes de `/clear`: resumir estado pendiente en la bóveda o en `docs/framework/SESSION.md` si el trabajo cruza sesiones.

### b) Auto-aprobación

- CLI configurado en `approvalMode: "unrestricted"` (auto-yes a lectura, edición y comandos no peligrosos).
- Backstop: `scripts/ade/guard.py` (hook `beforeShellExecution`) **sigue bloqueando** destructivos, push a main, secretos,
 producción. Aprobación humana obligatoria ahí.
- Validación cruzada permitida: cuando la tarea es de prioridad **Alta**, se puede abrir una segunda terminal con otro
 modelo (ej. `gpt-5.6-sol` + `claude-opus-5-thinking-high`) para contrastar diseño/plan antes de ejecutar.

### c) Multi-terminal / multi-modelo

- Permitido abrir terminales adicionales siempre que RAM y tokens lo soporten.
- Patrón de uso: una terminal "ejecutora" + una terminal "revisora" (otro modelo) sobre el mismo plan.
- Preferible usar subagentes (`Task`) en vez de abrir terminales manuales cuando el trabajo es independiente y acotado.

## Estilo de escritura

- **Idioma:** español para explicaciones; código, identificadores, commits y nombres de archivo en inglés.
- **Tono:** directo, sin relleno. "Lazy senior dev" (`.cursor/rules/ponytail.mdc`). Nada de "estoy encantado de ayudarte".
- **Documentos:** describen lo que **existe**. Lo futuro va marcado como "Planned".
- **Commits:** `<verbo imperativo>: <qué y por qué>`. No "updates".
- **PRs / mensajes:** una pantalla máximo. Problema → cambio → verificación.
- **Diagramas:** Mermaid dentro de Markdown (nativo en Obsidian y en GitHub).
