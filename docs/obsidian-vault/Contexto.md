# Contexto

## Organización

- **Empresa:** Belcorp.
- **Área:** Automatizaciones e IA.
- **Owner humano:** Mauricio Linares (Software Engineer).
- **Workspace:** `C:\Users\mauriciolinares\Investigaciones`.

## Qué hacemos aquí

Este repo es el **ADE** (Agentic Development Environment) de Mauricio: un conjunto de reglas, skills y subagentes de Cursor
para investigar, diseñar, construir y revisar proyectos de automatización e IA para Belcorp con calidad consistente,
sin depender de la memoria de un único modelo ni de la disciplina manual.

No es un producto final. Es la **fábrica** desde donde salen los proyectos (cada proyecto real va en su propio repo o
subcarpeta y arranca con [[Plantilla-Proyecto-SRS]]).

## Usuario primario

- **Mauricio** usando Cursor (CLI + IDE) sobre Windows / PowerShell.
- Prefiere trabajar directamente en código (crear, debuggear, iterar).
- Idioma por defecto para interacción: **español**. Código, nombres de archivo y commits: **inglés**.

## No-negociables (negocio + técnica)

- Datos de clientes / consultoras / consumidoras de Belcorp son **PII**: nunca en logs, nunca en prompts, nunca en commits.
- Cualquier integración con sistemas internos de Belcorp requiere revisión de seguridad antes de merge.
- Aprobación humana explícita para: producción, operaciones destructivas, cambios masivos, secretos/permisos,
 migraciones de datos. Enforced por `.cursor/rules/security.mdc` + `scripts/ade/guard.py`.
- No introducir dependencias nuevas sin justificación (`.cursor/rules/ponytail.mdc`).

## Enlaces vivos

- Reglas raíz: `.cursor/rules/`
- Agentes: `.cursor/agents/` → ver [[Equipo]]
- Skills: `.cursor/skills/` → ver [[Equipo]]
- Framework docs: `docs/framework/`
- Brief del proyecto activo: `PROJECT.md`
