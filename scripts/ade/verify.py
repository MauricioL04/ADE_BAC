#!/usr/bin/env python3
"""ADE verification gate: detect the project's real commands and run them.

Usage:
    python scripts/ade/verify.py            # run everything detected
    python scripts/ade/verify.py --list     # show detected commands, run nothing
    python scripts/ade/verify.py --no-secrets

Only commands that are backed by a manifest/config in the repository are run.
Nothing is invented: if a stage has no detected command it is reported as SKIP
(not applicable), never as PASS.

Exit code: 0 when no stage FAILED, 1 otherwise.
Each run is appended to .ade/runs.jsonl (local, git-ignored) as a minimal
observability trail.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

STAGES = ["build", "lint", "typecheck", "unit", "integration", "secrets"]

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


@dataclass
class Stage:
    name: str
    cmd: list[str] | None = None
    note: str = ""
    status: str = SKIP
    output: str = ""
    seconds: float = 0.0


@dataclass
class Plan:
    stack: list[str] = field(default_factory=list)
    stages: dict[str, Stage] = field(default_factory=dict)


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _node_pm(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def detect(root: Path) -> Plan:
    plan = Plan(stages={n: Stage(n) for n in STAGES if n != "secrets"})
    s = plan.stages

    # ---- Node ----------------------------------------------------------
    pkg = root / "package.json"
    if pkg.exists():
        plan.stack.append("node")
        try:
            scripts = json.loads(_read(pkg)).get("scripts", {}) or {}
        except json.JSONDecodeError:
            scripts = {}
        pm = _node_pm(root)
        run = [pm, "run"] if pm != "npm" else ["npm", "run", "--silent"]
        mapping = {
            "build": ["build"],
            "lint": ["lint"],
            "typecheck": ["typecheck", "type-check", "tsc"],
            "unit": ["test", "test:unit"],
            "integration": ["test:integration", "test:e2e"],
        }
        for stage, names in mapping.items():
            for n in names:
                if n in scripts:
                    s[stage].cmd = run + [n]
                    s[stage].note = f"{pm} script '{n}'"
                    break

    # ---- Python --------------------------------------------------------
    py_files = [p for p in root.rglob("*.py") if not _ignored(p, root)]
    pyproject = root / "pyproject.toml"
    py_text = _read(pyproject)
    if py_files or pyproject.exists() or (root / "requirements.txt").exists():
        plan.stack.append("python")
        py = sys.executable or "python"
        if s["build"].cmd is None and py_files:
            s["build"].cmd = [py, "-m", "compileall", "-q"] + _py_roots(root)
            s["build"].note = "python compileall (syntax check)"
        if s["lint"].cmd is None and ("[tool.ruff" in py_text or (root / "ruff.toml").exists()):
            s["lint"].cmd = [py, "-m", "ruff", "check", "."]
            s["lint"].note = "ruff (configured)"
        if s["typecheck"].cmd is None and ("[tool.mypy" in py_text or (root / "mypy.ini").exists()):
            s["typecheck"].cmd = [py, "-m", "mypy", "."]
            s["typecheck"].note = "mypy (configured)"
        tests_dir = root / "tests"
        has_tests = tests_dir.is_dir() and any(tests_dir.rglob("test_*.py"))
        if s["unit"].cmd is None and has_tests:
            if "[tool.pytest" in py_text or (root / "pytest.ini").exists():
                s["unit"].cmd = [py, "-m", "pytest", "-q"]
                s["unit"].note = "pytest (configured)"
            else:
                s["unit"].cmd = [py, "-m", "unittest", "discover", "-s", "tests"]
                s["unit"].note = "unittest discover (tests/)"

    # ---- Go ------------------------------------------------------------
    if (root / "go.mod").exists():
        plan.stack.append("go")
        s["build"].cmd = s["build"].cmd or ["go", "build", "./..."]
        s["lint"].cmd = s["lint"].cmd or ["go", "vet", "./..."]
        s["unit"].cmd = s["unit"].cmd or ["go", "test", "./..."]
        for st in ("build", "lint", "unit"):
            s[st].note = s[st].note or "go toolchain"

    # ---- Rust ----------------------------------------------------------
    if (root / "Cargo.toml").exists():
        plan.stack.append("rust")
        s["build"].cmd = s["build"].cmd or ["cargo", "build"]
        s["lint"].cmd = s["lint"].cmd or ["cargo", "clippy", "--", "-D", "warnings"]
        s["unit"].cmd = s["unit"].cmd or ["cargo", "test"]
        for st in ("build", "lint", "unit"):
            s[st].note = s[st].note or "cargo toolchain"

    # ---- Not auto-detected stacks -------------------------------------
    for marker, name in (("pom.xml", "maven"), ("build.gradle", "gradle"),
                         ("build.gradle.kts", "gradle"), ("*.csproj", "dotnet")):
        if list(root.glob(marker)):
            plan.stack.append(name)
            plan.stages["build"].note = plan.stages["build"].note or (
                f"{name} detected but not auto-wired: add commands in scripts/ade/verify.py")
    return plan


def _py_roots(root: Path) -> list[str]:
    return [d for d in ("scripts", "src", "tests", "app") if (root / d).is_dir()] or ["."]


def _ignored(path: Path, root: Path) -> bool:
    parts = set(path.relative_to(root).parts)
    return bool(parts & {".git", "node_modules", ".venv", "venv", "__pycache__", ".ade", "dist", "build"})


# --------------------------------------------------------------------------
# Secret scan (cheap, deterministic, no dependencies)
# --------------------------------------------------------------------------

SECRET_PATTERNS = {
    "AWS access key id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "Hardcoded credential": re.compile(
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|token)\b\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"),
}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".exe", ".dll", ".pyc"}
ALLOW_MARKER = "ade:allow-secret"


def _candidate_files(root: Path) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard"], cwd=root,
            capture_output=True, text=True, check=True).stdout.splitlines()
        return [root / p for p in out if p]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in root.rglob("*") if p.is_file() and not _ignored(p, root)]


def scan_secrets(root: Path) -> list[str]:
    findings: list[str] = []
    for f in _candidate_files(root):
        if not f.is_file() or f.suffix.lower() in BINARY_EXT or f.stat().st_size > 1_000_000:
            continue
        if f.name == ".env" or f.name.startswith(".env."):
            if f.name not in (".env.example", ".env.sample", ".env.template"):
                findings.append(f"{f.relative_to(root)}: env file present (must not be committed)")
        for i, line in enumerate(_read(f).splitlines(), 1):
            if ALLOW_MARKER in line:
                continue
            for label, rx in SECRET_PATTERNS.items():
                if rx.search(line):
                    findings.append(f"{f.relative_to(root)}:{i}: {label}")
    return findings


# --------------------------------------------------------------------------
# Execution and reporting
# --------------------------------------------------------------------------

def run_stage(stage: Stage, root: Path, timeout: int = 600) -> None:
    if not stage.cmd:
        stage.status = SKIP
        return
    t0 = time.time()
    try:
        proc = subprocess.run(stage.cmd, cwd=root, capture_output=True, text=True,
                              shell=False, timeout=timeout)
        stage.status = PASS if proc.returncode == 0 else FAIL
        stage.output = (proc.stdout + proc.stderr).strip()
    except FileNotFoundError as exc:
        stage.status = FAIL
        stage.output = f"tool not found: {exc}"
    except subprocess.TimeoutExpired:
        stage.status = FAIL
        stage.output = f"timed out after {timeout}s"
    stage.seconds = round(time.time() - t0, 2)


def render(plan: Plan, secrets: list[str] | None, regression: str) -> str:
    def st(name: str) -> str:
        return plan.stages[name].status

    lines = ["TEST REPORT", "", f"Stack: {', '.join(plan.stack) or 'none detected'}", ""]
    rows = [("Build", st("build")), ("Unit Tests", st("unit")),
            ("Integration Tests", st("integration")), ("Regression", regression),
            ("Lint", st("lint")), ("Type Check", st("typecheck"))]
    if secrets is not None:
        rows.append(("Secret Scan", FAIL if secrets else PASS))
    for label, status in rows:
        lines += [f"{label}:", status if status != SKIP else "SKIP (not applicable: no command detected)", ""]
    lines.append("Remaining Issues:")
    issues = [f"- {s.name}: {s.note or s.cmd} failed\n{_indent(s.output)}"
              for s in plan.stages.values() if s.status == FAIL]
    issues += [f"- secret: {f}" for f in (secrets or [])]
    lines += issues or ["- none"]
    return "\n".join(lines)


def to_dict(plan: Plan, secrets: list[str] | None, regression: str) -> dict:
    """Machine-readable result (used by --json). SKIP stays SKIP; it is never PASS."""
    stages = {n: s.status for n, s in plan.stages.items()}
    stages["regression"] = regression
    failed = any(s.status == FAIL for s in plan.stages.values()) or bool(secrets)
    return {
        "stack": plan.stack,
        "stages": stages,
        "secrets": {"status": SKIP if secrets is None else (FAIL if secrets else PASS),
                    "findings": secrets or []},
        "ok": not failed,
    }


def _indent(text: str, n: int = 4, limit: int = 40) -> str:
    rows = text.splitlines()[-limit:]
    return "\n".join(" " * n + r for r in rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repository root (default: cwd)")
    ap.add_argument("--list", action="store_true", help="show detected commands and exit")
    ap.add_argument("--no-secrets", action="store_true", help="skip the secret scan")
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON instead of the text report")
    ap.add_argument("--timeout", type=int, default=600, help="seconds allowed per stage (default: 600)")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    plan = detect(root)
    if args.list:
        print(f"Stack: {', '.join(plan.stack) or 'none detected'}")
        for s in plan.stages.values():
            print(f"{s.name:12} {' '.join(s.cmd) if s.cmd else '-'}  {('(' + s.note + ')') if s.note else ''}")
        return 0

    for stage in plan.stages.values():
        run_stage(stage, root, args.timeout)
    secrets = None if args.no_secrets else scan_secrets(root)

    # "Regression" = the existing test suite (unit + integration) passing as a whole.
    ran = [plan.stages[n].status for n in ("unit", "integration") if plan.stages[n].status != SKIP]
    regression = SKIP if not ran else (FAIL if FAIL in ran else PASS)

    if args.json:
        print(json.dumps(to_dict(plan, secrets, regression), indent=2))
    else:
        print(render(plan, secrets, regression))

    failed = any(s.status == FAIL for s in plan.stages.values()) or bool(secrets)
    log = root / ".ade"
    log.mkdir(exist_ok=True)
    with (log / "runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "stack": plan.stack,
            "stages": {n: s.status for n, s in plan.stages.items()},
            "secret_findings": len(secrets or []),
            "ok": not failed,
        }) + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
