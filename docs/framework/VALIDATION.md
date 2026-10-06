# Framework validation run (no deployment)

Date: 2026-09-29. Real run of the pipeline on a small task; every result below was observed, not assumed.

**Goal**: the git rule says "do not push to main/master directly" but `scripts/ade/guard.py` did not enforce it.

## Route (orchestrator)

Simple change (2 files, no destructive step): research -> plan -> implement (TDD) -> test -> review -> security -> ponytail -> docs.

## Research (FACT)

`.cursor/rules/git.mdc` requires it; `guard.py` `RULES` had no push-to-main rule (read the file). Cursor hooks return `permission: ask` (hooks doc).

## Plan

Add one rule to `RULES` + tests in `tests/test_ade_tools.py`; no new files, no dependencies. Risk: false positives (`feature/main`). Rollback: revert the two edits. No approval gate needed.

## Implement (test first)

Added `ask`/`allow` cases -> `python -m unittest tests.test_ade_tools` failed (`'allow' != 'ask'`) -> added the rule -> green.

## Test

`python scripts/ade/verify.py`: Build PASS, Unit PASS, Regression PASS, Secret Scan PASS; Integration/Lint/Type Check SKIP (no command detected).
A structure test failed once and caught a real stale reference (`testing.mdc` -> old `tester` skill path) and a BOM problem class; both fixed.

## Review and Security (two independent subagents, read-only, in parallel)

Run as general-purpose subagents instructed to follow `.cursor/agents/reviewer.md` / `security.md`, because project subagents are not exposed as Task types here.

- Reviewer: **H1** rule bypassed by `git -C x push origin main`, quoted refs, `main;`; **M1** false positives from `... && git checkout main`; M3 unquoted secrets not redacted in the log; L1/L4/L5 test gaps. Recommendation: APPROVE WITH CHANGES.
- Security: **CONFIRMED** C1 (redaction gaps: PEM body, bearer, URI credentials, unquoted assignments), C2 (log in a versioned folder), C3 (log entry forgery / markup); POTENTIAL P1 (guard bypasses), P3 (root taken from payload), P4 (manual fallback via argv). FALSE POSITIVE: Ponytail files contain no hidden instructions. Recommendation: PASS WITH CONDITIONS.

## Fix loop (coder -> tester)

Guard prefix/tail generalized and split at shell separators; the initial log redaction was improved, bodies were made safe,
the log root was fixed to the repo (payload ignored), the manual fallback moved to stdin, prompts always allow on failure,
and the log was git-ignored; tests were added for each finding.
Re-run: 26 tests pass, `verify.py` all applicable stages PASS. P2 (fail-open when Python is missing) and P5 (no file locking) are accepted, documented limits.

## Ponytail pass

The reviewer ran the ponytail lens over the diff: `net: -0 lines possible` (kept: `--manual` and `--root`, both tested). During the fix loop the
"trust `workspace_roots` from the payload" code was **deleted** (less code and closes P3).

## Documentation

`GOVERNANCE.md`, `README.md`, `interaction-log.mdc`, ADR-0002, this file.

## Empty-window limitation resolved

**Observed FACT**: Cursor's Hooks output reported "No workspace folder found, project hooks will not be available"; the log
contained no entries for prompts sent after project hooks were written. The user-level hooks file did not exist.

Added `install_cursor_hooks.py` and installed its scoped fallback in `~/.cursor/hooks.json`. It runs only for an empty
workspace whose `transcript_path` contains this project's Cursor marker, so it neither captures other projects nor duplicates
the project hook when a folder is open. It preserves unrelated hooks, validates JSON before writing, is idempotent and has an
uninstall command. The logger now serializes concurrent appends via an OS file lock.

**Live command validation**: invoked each installed command with a documented payload and this project's transcript marker:
`beforeSubmitPrompt` returned `{"continue": true}`; `afterAgentResponse` returned no stdout; both created their expected entries
in `docs/framework/log/2026-09-29.md`. Tests cover the same scope, installer preservation/idempotence/malformed-config refusal,
and concurrent appends. Final suite: 35 tests PASS; `verify.py` PASS for every applicable stage.

## Follow-up review fixes

A second independent review found: user-hook removal matched a generic flag, transcript matching was a substring, the
installer's read-modify-write was unlocked, and thread-only testing did not prove multiprocess writes. A second security
review found that even aggressive redaction cannot guarantee that raw prompts/responses contain no personal data.

Fixed: hooks now match this project's canonical script path; transcript attribution matches the exact
`/projects/<marker>/agent-transcripts/` component; installer update uses an OS lock and unique same-directory temp file;
both thread and multiprocess appends are tested; metadata is sanitized. The fallback also installs the scoped shell guard.
The interaction log became a metadata-only audit; legacy files are reset (not parsed) with `log_interaction.py --scrub`.

The final security review caught three follow-up defects: a forged legacy H2 heading could survive scrub, a manual here-string
could enter PowerShell history, and script ownership matching still accepted a path prefix. Fixed: scrub resets whole legacy
files; manual fallback accepts character counts only; ownership uses a script-path boundary. The guard now asks before a
`git push` that contains an unexpanded variable reference, and the audit refuses a resolved path outside the repository.

## Remaining platform limits

- A Cursor conversation with neither workspace root nor `transcript_path` cannot be safely attributed to this repo. It is
  intentionally skipped rather than logging another project's interaction here.
- Rule/skill automatic loading and description-based subagent delegation remain Cursor features; the framework validates the
  files but cannot force the desktop client to invoke them.
