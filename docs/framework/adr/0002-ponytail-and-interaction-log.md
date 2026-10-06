# ADR-0002: Ponytail as an always-on rule; hook-based interaction log

## Context

The user asked for (1) Ponytail (anti-over-engineering) as a transversal layer, installed from the official repository, and
(2) a mandatory record of every query and response. Inspected upstream `DietrichGebert/ponytail` @ `e3ba2aa` (v4.10.0): it offers
a Cursor rule (`.cursor/rules/ponytail.mdc`), skills, and an optional `hooks.json` installer; its docs state rule and hooks are
alternatives. Cursor hooks documentation lists `beforeSubmitPrompt` (input `prompt`) and `afterAgentResponse` (input `text`).

## Decision

- Install the upstream rule and the `ponytail-review` skill verbatim; keep project-specific limits in our own rules/skills so the
  vendor files stay updatable. Do not install Ponytail's hooks (excluded by the rule, needs Node, adds latency).
- Implement the interaction **audit** with two Cursor hooks calling one stdlib script, plus a rule that makes it mandatory
  and a stdin fallback. Persist only role and character count; raw content remains in
  Cursor's transcript. This resolves the conflict between complete event accountability and the rule never to write
  secrets or personal data into repository logs. Write only under the repo, fail open and git-ignore it by default.
- The observed Cursor empty-window mode does not load project hooks. Install a user-level fallback with
  `install_cursor_hooks.py`; it runs only if the conversation has no workspace root and its transcript path identifies this
  repository. It preserves unrelated user hooks and is reversible.

## Alternatives

- Ponytail hooks installer: rejected (conflicts with the rule per upstream docs; Node dependency; ~1 s/prompt on Windows).
- All Ponytail skills: rejected for now (duplicate instructions, context cost); copy from upstream if needed.
- Log by agent instruction only: rejected (unreliable; the user made it mandatory). Kept only as fallback.
- Version the audit: rejected by default; raw content cannot be enabled in the project audit.
- Global logging without a project transcript check: rejected (would capture unrelated Cursor conversations in this repository).

## Consequences

+ Mechanical, low-code logging; Ponytail updates are a file copy after review.
- `afterAgentResponse` may fire per assistant message, so a turn can produce several entries.
- Hook execution and payload shapes depend on Cursor versions (documented fields used only).
- A conversation without both a workspace root and transcript path cannot be safely attributed, so the fallback skips it.
- Legacy audit files are reset rather than parsed, because old message text could forge an apparent entry heading.
- Third-party prompt content is loaded into every session: review on every upstream update.

## Status

Accepted
