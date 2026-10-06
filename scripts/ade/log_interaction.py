#!/usr/bin/env python3
"""ADE interaction log: document every user query and assistant response.

Wired as Cursor hooks (see .cursor/hooks.json):
  beforeSubmitPrompt   stdin {"prompt": ...}  -> logs the user query, answers {"continue": true}
  afterAgentResponse   stdin {"text": ...}    -> logs the assistant response

Entries go to docs/framework/log/YYYY-MM-DD.md under this repository (the path never comes
from the payload). They record the role, conversation and body size only; full prompt/response
content stays in Cursor's transcript and is never duplicated in a project file. This avoids
retaining secrets, personal data or business data. The hook never blocks the user: on any
failure it prints a note on stderr and still allows the prompt.

Manual fallback (hooks unavailable), JSON on stdin:
  python scripts/ade/log_interaction.py --manual --user-chars 42 --assistant-chars 99
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import sys
import time
import threading
from contextlib import contextmanager
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = Path("docs") / "framework" / "log"
THREAD_APPEND_LOCK = threading.Lock()

def project_transcript_marker(root: Path = DEFAULT_ROOT) -> str:
    """Return Cursor's project-directory marker for this workspace."""
    return str(root.resolve()).replace(":", "").replace("\\", "-").replace("/", "-").lower()


def should_log(payload: dict, empty_workspace_only: bool) -> bool:
    """Keep the user-level hook scoped to this project and avoid duplicate entries."""
    if not empty_workspace_only:
        return True
    if payload.get("workspace_roots"):
        return False
    transcript = posixpath.normpath(str(payload.get("transcript_path") or "").replace("\\", "/")).lower()
    expected = f"/projects/{project_transcript_marker()}/agent-transcripts/"
    return expected in transcript + "/"


def _require_under_root(root: Path, path: Path) -> Path:
    def normalized(candidate: Path) -> str:
        value = os.path.normcase(os.path.normpath(str(candidate.resolve())))
        return value[4:] if value.startswith("\\\\?\\") else value

    resolved_root = normalized(root)
    resolved_path = normalized(path)
    try:
        is_inside = os.path.commonpath([resolved_root, resolved_path]) == resolved_root
    except ValueError:
        is_inside = False
    if not is_inside:
        raise OSError(f"refusing to write outside audit root: {resolved_path}")
    return path


@contextmanager
def _locked_append(path: Path):
    """Serialize appenders so simultaneous hooks cannot interleave log entries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    # Windows byte-range locks are process-scoped, so they do not serialize sibling threads.
    # Keep this small process lock as well as the OS lock for separate hook processes.
    with THREAD_APPEND_LOCK, lock_path.open("a+b") as lock:
        try:
            if os.name == "nt":
                import msvcrt
                if lock.tell() == 0:
                    lock.write(b"\0")
                    lock.flush()
                    lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            new_file = not path.exists()
            with path.open("a", encoding="utf-8", newline="\n") as fh:
                yield fh, new_file
        finally:
            try:
                if os.name == "nt":
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass


def append_entry(root: Path, role: str, text: str = "", meta: str = "", now: float | None = None,
                 characters: int | None = None) -> Path:
    stamp = time.localtime(now if now is not None else time.time())
    path = _require_under_root(root, root / LOG_DIR / (time.strftime("%Y-%m-%d", stamp) + ".md"))
    safe_meta = re.sub(r"[^A-Za-z0-9_-]", "", meta)[:32]
    count = len(text) if characters is None else characters
    if count < 0:
        raise ValueError("character count cannot be negative")
    body = f"    content: withheld by privacy policy ({count} characters)\n"
    header = f"## {time.strftime('%H:%M:%S', stamp)} - {role}" + (f" ({safe_meta})" if safe_meta else "")
    with _locked_append(path) as (fh, new_file):
        if new_file:
            fh.write(f"# Interaction audit {time.strftime('%Y-%m-%d', stamp)}\n\n")
        fh.write(f"{header}\n\n{body}\n")
    return path


def handle_hook(payload: dict, root: Path) -> None:
    event = payload.get("hook_event_name", "")
    if event == "beforeSubmitPrompt" or ("prompt" in payload and "text" not in payload):
        append_entry(root, "USER", str(payload.get("prompt", "")))
    elif event == "afterAgentResponse" or "text" in payload:
        append_entry(root, "ASSISTANT", str(payload.get("text", "")))


def scrub_logs(root: Path) -> int:
    """Reset legacy logs whose raw bodies cannot be distinguished from forged headings."""
    count = 0
    for path in sorted((root / LOG_DIR).glob("*.md")):
        _require_under_root(root, path)
        date = path.stem
        path.write_text(
            f"# Interaction audit {date}\n\nLegacy entries reset by privacy scrub; no message content retained.\n",
            encoding="utf-8", newline="\n")
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manual", action="store_true", help="append metadata-only entries without passing message text")
    ap.add_argument("--scrub", action="store_true", help="remove bodies from existing local interaction logs")
    ap.add_argument("--user-chars", type=int, help="manual user-message character count")
    ap.add_argument("--assistant-chars", type=int, help="manual assistant-message character count")
    ap.add_argument("--conversation-id", default="", help="manual conversation identifier (sanitized before storage)")
    ap.add_argument("--empty-workspace-only", action="store_true",
                    help="log only a no-workspace Cursor conversation whose transcript belongs to this project")
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="log root (tests only)")
    args = ap.parse_args(argv)
    root = Path(args.root)

    if args.scrub:
        try:
            print(f"Scrubbed {scrub_logs(root)} interaction log file(s).")
            return 0
        except OSError as exc:
            print(f"ade log_interaction: {exc}", file=sys.stderr)
            return 1

    if args.manual:
        try:
            if args.user_chars is None and args.assistant_chars is None:
                raise ValueError("manual mode requires --user-chars and/or --assistant-chars")
            meta = f"manual-{args.conversation_id}" if args.conversation_id else "manual"
            if args.user_chars is not None:
                append_entry(root, "USER", meta=meta, characters=args.user_chars)
            if args.assistant_chars is not None:
                append_entry(root, "ASSISTANT", meta=meta, characters=args.assistant_chars)
        except (OSError, ValueError) as exc:
            print(f"ade log_interaction: {exc}", file=sys.stderr)
            return 1
        return 0

    payload: dict = {}
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig") or "{}")
        if should_log(payload, args.empty_workspace_only):
            handle_hook(payload, root)
    except Exception as exc:  # never break the user's flow because of logging
        print(f"ade log_interaction: {exc}", file=sys.stderr)
    is_response = payload.get("hook_event_name") == "afterAgentResponse" or "text" in payload
    if not is_response:
        print(json.dumps({"continue": True}))  # always allow the prompt, even if logging failed
    return 0


if __name__ == "__main__":
    sys.exit(main())
