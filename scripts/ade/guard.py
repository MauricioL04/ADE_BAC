#!/usr/bin/env python3
"""ADE human-approval gate, wired as a Cursor `beforeShellExecution` hook.

Cursor sends JSON on stdin (field `command`); this script answers with
{"permission": "allow" | "ask", ...}. Destructive or irreversible commands
return "ask" so the human decides. Nothing is ever silently auto-approved by
this script; it only *adds* friction, it never grants permissions.

The same rules are exposed as `evaluate()` for unit tests.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from log_interaction import should_log

# (category, regex). Case-insensitive. Keep patterns specific to limit false positives.
# `git [-C x | -c k=v | --opt]... push`, then arguments up to the next shell separator (so `push x && git checkout main` is not a push to main).
GIT_PUSH = r"\bgit\b(?:\s+(?:-C\s+\S+|-c\s+\S+|--\S+))*\s+push\b[^;&|\n]*"

RULES: list[tuple[str, str]] = [
    ("git: force push", GIT_PUSH + r"(?:\s--force(?!-with-lease)\b|\s-f\b|\s\+\S+)"),
    ("git: push to main/master", GIT_PUSH + r"(?:\s|:|refs/heads/|[\"'+])(?:main|master)(?=[\s\"';&|)]|$)"),
    ("git: push with variable ref", GIT_PUSH + r".*(?:\$\{?|\%[A-Za-z_]|![A-Za-z_])"),
    ("git: destructive history/worktree change", r"\bgit\s+(?:reset\s+--hard|clean\s+-\w*[fd]|checkout\s+--\s|branch\s+-D|rebase\b.*--root)"),
    ("git: bypass hooks", r"\bgit\s+(?:commit|push)\b.*--no-verify"),
    ("filesystem: recursive delete", r"(?:\brm\s+-\w*[rR]\w*[fF]?\b|\brm\s+-\w*[fF]\w*[rR]\b|Remove-Item\b.*-Recurse|\brmdir\s+/s\b|\bdel\s+/[sfq]\b)"),
    ("sql: destructive statement", r"\b(?:drop\s+(?:database|table|schema|user|index)|truncate\s+table|truncate\s+\w+|alter\s+table\s+\w+\s+drop|purge\s+recyclebin|flashback\s+database)\b"),
    ("sql: DELETE/UPDATE without WHERE", r"\b(?:delete\s+from\s+\w+|update\s+\w+\s+set\b)"),
    ("deploy: production-affecting command", r"\b(?:terraform\s+(?:apply|destroy)|kubectl\s+(?:apply|delete|rollout|scale)|helm\s+(?:install|upgrade|uninstall)|docker\s+push|docker\s+compose\s+.*\bup\b.*prod|npm\s+publish|twine\s+upload|gh\s+release\s+create|aws\s+\S+\s+(?:delete|terminate|deploy)|az\s+\S+\s+delete|gcloud\s+\S+\s+(?:delete|deploy))\b"),
    ("secrets: env/credential files", r"(?:\b(?:cat|type|Get-Content|cp|copy|mv|move|Remove-Item|rm)\b.*(?:\.env(?!\.example|\.sample)\b|id_rsa|\.pem\b|credentials))"),
    ("permissions: broad chmod/chown", r"\b(?:chmod\s+(?:-R\s+)?7[0-7][0-7]|chown\s+-R|icacls\b.*\/grant)"),
]

COMPILED = [(name, re.compile(rx, re.IGNORECASE)) for name, rx in RULES]


def evaluate(command: str) -> tuple[str, str]:
    """Return (permission, category). permission is 'allow' or 'ask'."""
    for name, rx in COMPILED:
        if rx.search(command):
            # A DELETE/UPDATE that does contain WHERE is not flagged.
            if name.startswith("sql: DELETE/UPDATE") and re.search(r"\bwhere\b", command, re.IGNORECASE):
                continue
            return "ask", name
    return "allow", ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--empty-workspace-only", action="store_true",
                    help="apply only to this project's no-workspace Cursor conversation")
    args = ap.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
        command = str(payload.get("command", ""))
    except (json.JSONDecodeError, AttributeError):
        # Unparseable input: do not block normal work, Cursor's own approval still applies.
        print(json.dumps({"permission": "allow"}))
        return 0

    if args.empty_workspace_only and not should_log(payload, True):
        print(json.dumps({"permission": "allow"}))
        return 0

    permission, category = evaluate(command)
    if permission == "ask":
        print(json.dumps({
            "permission": "ask",
            "user_message": f"ADE approval gate [{category}]: review this command before it runs.",
            "agent_message": (
                f"Blocked pending human approval ({category}). Follow the ADE gate: "
                "explain impact, provide rollback, and wait for explicit approval. "
                "For SQL: ANALYZE -> GENERATE SCRIPT -> SHOW IMPACT -> HUMAN APPROVAL -> EXECUTE."),
        }))
    else:
        print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
