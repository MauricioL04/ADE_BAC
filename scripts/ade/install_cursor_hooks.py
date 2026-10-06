#!/usr/bin/env python3
"""Install or remove ADE's project-scoped fallback Cursor hooks at user scope.

Cursor does not load project hooks for a conversation opened in an empty window.
The installed hooks run only when there is no workspace root *and* Cursor's
transcript path identifies this repository, so they neither affect other
projects nor duplicate the project hooks when this folder is open.

Usage:
    python scripts/ade/install_cursor_hooks.py --install-user
    python scripts/ade/install_cursor_hooks.py --uninstall-user
    python scripts/ade/install_cursor_hooks.py --show
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from copy import deepcopy
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
USER_HOOKS = Path.home() / ".cursor" / "hooks.json"
LOGGER = ROOT / "scripts" / "ade" / "log_interaction.py"
GUARD = ROOT / "scripts" / "ade" / "guard.py"
SCRIPTS = {
    "beforeShellExecution": GUARD,
    "beforeSubmitPrompt": LOGGER,
    "afterAgentResponse": LOGGER,
}


def command(script: Path, python: str = sys.executable) -> str:
    return f'"{python}" "{script}" --empty-workspace-only'


def is_our_hook(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    value = str(entry.get("command", "")).replace("\\", "/").lower()
    scripts = [str(path.resolve()).replace("\\", "/").lower() for path in set(SCRIPTS.values())]
    return "--empty-workspace-only" in value and any(
        re.search(rf'(?<![a-z0-9._/-]){re.escape(path)}(?=["\s])', value) for path in scripts)


def load(path: Path) -> dict:
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError(f"{path} or its parent is a symlink; it was not changed")
    if not path.exists():
        return {"version": 1, "hooks": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON; it was not changed: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict):
        raise ValueError(f"{path} does not have a hooks object; it was not changed")
    data.setdefault("version", 1)
    data.setdefault("hooks", {})
    return data


def configure(data: dict, action: str, python: str = sys.executable) -> dict:
    """Return a copy with only this project's fallback hooks added or removed."""
    out = deepcopy(data)
    hooks = out.setdefault("hooks", {})
    for event, script in SCRIPTS.items():
        current = hooks.get(event, [])
        if not isinstance(current, list):
            raise ValueError(f"hooks.{event} must be a list; it was not changed")
        kept = [entry for entry in current if not is_our_hook(entry)]
        if action == "install":
            kept.append({"command": command(script, python), "timeout": 10})
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    return out


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(rendered)
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


@contextmanager
def locked(path: Path):
    """Serialize user-config read-modify-write across installer processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".ade.lock")
    with lock_path.open("a+b") as lock:
        if lock.tell() == 0:
            lock.write(b"\0")
            lock.flush()
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install-user", action="store_true")
    group.add_argument("--uninstall-user", action="store_true")
    group.add_argument("--show", action="store_true")
    parser.add_argument("--path", type=Path, default=USER_HOOKS, help="user hooks file (tests only)")
    args = parser.parse_args(argv)

    try:
        with locked(args.path):
            before = load(args.path)
            if args.show:
                print(json.dumps({"path": str(args.path), "configured": any(
                    is_our_hook(e) for event in SCRIPTS for e in before["hooks"].get(event, []))}, indent=2))
                return 0
            after = configure(before, "install" if args.install_user else "uninstall")
            write(args.path, after)
    except (OSError, ValueError) as exc:
        print(f"ADE hook installation failed: {exc}", file=sys.stderr)
        return 1
    verb = "Installed" if args.install_user else "Removed"
    print(f"{verb} ADE empty-workspace fallback hooks in {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
