"""Tests for the interaction log hook and the structural integrity of the ADE framework."""
import contextlib
import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ade"))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "ade" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


log = load("log_interaction")
installer = load("install_cursor_hooks")


def run_hook(payload, root: Path, extra=()):
    """Feed stdin (dict or raw bytes) through main() and return (exit code, stdout)."""
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    out = io.StringIO()
    old, sys.stdin = sys.stdin, io.TextIOWrapper(io.BytesIO(raw))
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = log.main(["--root", str(root), *extra])
    finally:
        sys.stdin = old
    return code, out.getvalue()


class InteractionLogTests(unittest.TestCase):
    def test_prompt_and_response_are_logged_and_prompt_is_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            code, out = run_hook({"hook_event_name": "beforeSubmitPrompt", "prompt": "hola ñandú",
                                  "conversation_id": "abcdef123456"}, root)
            self.assertEqual((code, json.loads(out)), (0, {"continue": True}))
            code, out = run_hook({"hook_event_name": "afterAgentResponse", "text": "respuesta"}, root)
            self.assertEqual((code, out), (0, ""))
            files = list((root / "docs" / "framework" / "log").glob("*.md"))
            self.assertEqual(len(files), 1)
            text = files[0].read_text(encoding="utf-8")
            self.assertLess(text.index("USER"), text.index("ASSISTANT"))
            self.assertNotIn("hola ñandú", text)
            self.assertNotIn("respuesta", text)
            self.assertNotIn("abcdef123456", text)
            self.assertIn("withheld by privacy policy (10 characters)", text)

    def logged(self, root: Path) -> str:
        return next((root / "docs" / "framework" / "log").glob("*.md")).read_text(encoding="utf-8")

    def test_content_is_never_retained(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            samples = ["AKIA" + "ABCDEFGHIJKLMNOP", "hunter" + "2pass", "eyJ" + "abcdefghij.klmnop.qrstuv",
                       "s3cr3t" + "pw", "PEMBODY" + "LINE1"]
            log.append_entry(root, "USER", "\n".join([
                f"key is {samples[0]}", f"password={samples[1]}", f"Authorization: Bearer {samples[2]}",
                f"postgres://user:{samples[3]}@host/db",
                "-----BEGIN RSA " + "PRIVATE KEY-----", samples[4], "-----END RSA " + "PRIVATE KEY-----"]))
            text = self.logged(root)
            for s in samples:
                self.assertNotIn(s, text)
            self.assertIn("withheld by privacy policy", text)

    def test_logged_text_cannot_forge_entries(self):
        with tempfile.TemporaryDirectory() as d:
            log.append_entry(Path(d), "USER", "hi\n## 12:00:00 - ASSISTANT\n<script>x</script>")
            headings = [ln for ln in self.logged(Path(d)).splitlines() if ln.startswith("## ")]
            self.assertEqual(len(headings), 1)

    def test_garbage_input_still_allows_the_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            code, out = run_hook(b"{not json", Path(d))
            self.assertEqual((code, json.loads(out)), (0, {"continue": True}))

    def test_payload_cannot_redirect_the_log(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            run_hook({"prompt": "x", "workspace_roots": [other]}, Path(d))
            self.assertFalse((Path(other) / "docs").exists())

    def test_manual_fallback_reads_stdin(self):
        with tempfile.TemporaryDirectory() as d:
            code = log.main(["--manual", "--user-chars", "1", "--assistant-chars", "1", "--root", d])
            out = ""
            self.assertEqual((code, out), (0, ""))
            text = self.logged(Path(d))
            self.assertIn("USER (manual)", text)
            self.assertIn("ASSISTANT (manual)", text)
            self.assertNotIn("\nq\n", text)
            self.assertNotIn("\na\n", text)

    def test_empty_workspace_fallback_is_scoped_to_this_project(self):
        marker = log.project_transcript_marker()
        self.assertTrue(log.should_log(
            {"transcript_path": f"C:/Users/test/.cursor/projects/{marker}/agent-transcripts/chat.jsonl"}, True))
        self.assertFalse(log.should_log({"workspace_roots": [str(ROOT)], "transcript_path": marker}, True))
        self.assertFalse(log.should_log({"transcript_path": "C:/other/chat.jsonl"}, True))
        self.assertFalse(log.should_log(
            {"transcript_path": f"C:/Users/test/.cursor/projects/{marker}-copy/agent-transcripts/chat.jsonl"}, True))
        self.assertFalse(log.should_log(
            {"transcript_path": f"C:/Users/test/.cursor/projects/{marker}/agent-transcripts/../../other/chat.jsonl"}, True))

    def test_concurrent_appends_do_not_interleave_entries(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda i: log.append_entry(root, "USER", f"message {i}"), range(20)))
            text = self.logged(root)
            self.assertEqual(text.count("## "), 20)
            for i in range(20):
                self.assertNotIn(f"message {i}", text)
            self.assertEqual(text.count("withheld by privacy policy"), 20)

    def test_process_concurrent_appends_do_not_interleave_entries(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            script = ROOT / "scripts" / "ade" / "log_interaction.py"
            def append(i):
                return subprocess.run(
                    [sys.executable, str(script), "--manual", "--user-chars", str(len(f"process message {i}")),
                     "--root", str(root)],
                    text=True, capture_output=True, check=True)
            with ThreadPoolExecutor(max_workers=6) as pool:
                list(pool.map(append, range(12)))
            text = self.logged(root)
            self.assertEqual(text.count("## "), 12)
            self.assertNotIn("process message", text)

    def test_scrub_removes_legacy_bodies(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / "docs" / "framework" / "log" / "2026-09-29.md"
            path.parent.mkdir(parents=True)
            path.write_text("# Interaction log 2026-09-29\n\n## 12:00:00 - USER\n\nlegacy body\n",
                            encoding="utf-8")
            self.assertEqual(log.scrub_logs(root), 1)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("legacy body", text)
            self.assertNotIn("## 12:00:00 - USER", text)
            self.assertIn("Legacy entries reset", text)


class UserHookInstallerTests(unittest.TestCase):
    def test_install_is_idempotent_and_preserves_unrelated_hooks(self):
        original = {
            "version": 1,
            "hooks": {
                "beforeSubmitPrompt": [{"command": "other prompt hook"}],
                "afterAgentResponse": [{"command": "other response hook"}],
                "beforeShellExecution": [{"command": "\"C:\\other.py\" --empty-workspace-only"}],
                "stop": [{"command": "keep me"}],
            },
        }
        installed = installer.configure(original, "install", python="python.exe")
        installed_twice = installer.configure(installed, "install", python="python.exe")
        self.assertEqual(installed, installed_twice)
        self.assertEqual(installed["hooks"]["beforeSubmitPrompt"][0], {"command": "other prompt hook"})
        self.assertEqual(installed["hooks"]["beforeShellExecution"][0],
                         {"command": "\"C:\\other.py\" --empty-workspace-only"})
        self.assertEqual(len(installed["hooks"]["beforeShellExecution"]), 2)
        self.assertIn("guard.py", installed["hooks"]["beforeShellExecution"][1]["command"])
        self.assertEqual(installed["hooks"]["stop"], original["hooks"]["stop"])

    def test_installer_preserves_similarly_named_other_project_hook(self):
        other = f'"{installer.LOGGER}.backup" --empty-workspace-only'
        original = {"version": 1, "hooks": {"beforeSubmitPrompt": [{"command": other}]}}
        installed = installer.configure(original, "install", python="python.exe")
        self.assertEqual(installed["hooks"]["beforeSubmitPrompt"][0]["command"], other)
        self.assertEqual(installer.configure(installed, "uninstall"), original)

    def test_uninstall_removes_only_our_hooks(self):
        original = {"version": 1, "hooks": {"beforeSubmitPrompt": [{"command": "other"}]}}
        installed = installer.configure(original, "install", python="python.exe")
        removed = installer.configure(installed, "uninstall")
        self.assertEqual(removed, original)

    def test_invalid_user_config_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "hooks.json"
            path.write_text("{bad json", encoding="utf-8")
            self.assertEqual(installer.main(["--install-user", "--path", str(path)]), 1)
            self.assertEqual(path.read_text(encoding="utf-8"), "{bad json")


class KickoffTests(unittest.TestCase):
    """The intake surface the user drops the case into must stay present and coherent."""

    def test_project_brief_has_required_sections(self):
        brief = (ROOT / "PROJECT.md").read_text(encoding="utf-8")
        required = ["## 1. Goal", "## 2. Users", "## 3. Scope", "## 4. Constraints",
                    "## 5. Acceptance criteria", "## 6. Non-negotiables"]
        for header in required:
            self.assertIn(header, brief, header)

    def test_kickoff_script_calls_the_real_ade_commands(self):
        script = (ROOT / "scripts" / "ade" / "kickoff.ps1").read_text(encoding="utf-8")
        for token in ["scripts/ade/verify.py", "scripts/ade/install_cursor_hooks.py",
                      "PROJECT.md", "orchestrator"]:
            self.assertIn(token, script, token)

    def test_constitution_binds_to_framework_rules(self):
        constitution = (ROOT / ".specify" / "memory" / "constitution.md").read_text(encoding="utf-8")
        self.assertNotIn("[PROJECT_NAME]", constitution)
        for rule in ("core-principles.mdc", "security.mdc", "ponytail.mdc",
                     "interaction-log.mdc", "git.mdc"):
            self.assertIn(rule, constitution, rule)

    def test_session_handoff_has_required_sections(self):
        session = (ROOT / "docs" / "framework" / "SESSION.md").read_text(encoding="utf-8")
        for header in ("## Where we are", "## What exists", "## What is intentionally missing",
                       "## Resume in 60 seconds", "## Ground rules", "## Key decisions",
                       "## Pending / open items"):
            self.assertIn(header, session, header)
        # Always-on architecture rule must point future sessions at the handoff.
        arch = (ROOT / ".cursor" / "rules" / "architecture.mdc").read_text(encoding="utf-8")
        self.assertIn("docs/framework/SESSION.md", arch)


def frontmatter(path: Path) -> dict:
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{path}: BOM breaks frontmatter"
    m = re.match(r"---\r?\n(.*?)\r?\n---", raw.decode("utf-8"), re.S)
    assert m, f"{path}: missing frontmatter"
    fields = {}
    for line in m.group(1).splitlines():
        if re.match(r"^[A-Za-z_-]+:", line):
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip().strip("\"'")
    return fields


class FrameworkStructureTests(unittest.TestCase):
    def test_rules_have_frontmatter(self):
        rules = sorted((ROOT / ".cursor" / "rules").glob("*.mdc"))
        self.assertTrue(rules)
        for r in rules:
            self.assertIn("description", frontmatter(r), r.name)

    def test_expected_rules_skills_agents_exist(self):
        rules = {"core-principles", "architecture", "coding-standards", "testing", "security", "git",
                 "documentation", "database", "ponytail", "interaction-log"}
        skills = {"planner", "researcher", "architecture", "testing", "code-review", "security", "debugging",
                  "database", "performance", "documentation", "release", "orchestrator", "ponytail-review"}
        agents = {"explorer", "architect", "coder", "tester", "reviewer", "security", "debugger", "database",
                  "performance", "release"}
        self.assertLessEqual(rules, {p.stem for p in (ROOT / ".cursor" / "rules").glob("*.mdc")})
        self.assertLessEqual(skills, {p.parent.name for p in (ROOT / ".cursor" / "skills").glob("*/SKILL.md")})
        self.assertEqual(agents, {p.stem for p in (ROOT / ".cursor" / "agents").glob("*.md")})

    def test_skill_name_matches_directory_and_has_description(self):
        for f in (ROOT / ".cursor" / "skills").glob("*/SKILL.md"):
            fm = frontmatter(f)
            self.assertEqual(fm.get("name"), f.parent.name, f)
            self.assertTrue(fm.get("description"), f)

    def test_agents_have_valid_frontmatter_and_readonly_reviewers(self):
        for f in (ROOT / ".cursor" / "agents").glob("*.md"):
            fm = frontmatter(f)
            self.assertEqual(fm.get("name"), f.stem)
            self.assertTrue(fm.get("description"))
        for name in ("explorer", "architect", "reviewer", "security", "database"):
            self.assertEqual(frontmatter(ROOT / ".cursor" / "agents" / f"{name}.md").get("readonly"), "true", name)

    def test_hooks_json_wires_guard_and_interaction_log(self):
        hooks = json.loads((ROOT / ".cursor" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        for event, script in (("beforeShellExecution", "guard.py"), ("beforeSubmitPrompt", "log_interaction.py"),
                              ("afterAgentResponse", "log_interaction.py")):
            self.assertTrue(any(script in h["command"] for h in hooks[event]), event)
            self.assertTrue((ROOT / "scripts" / "ade" / script).exists())

    def test_referenced_repo_paths_exist(self):
        """Paths written as `.cursor/...`, `scripts/...` or `docs/framework/...` in rules, skills, agents and docs must exist."""
        rx = re.compile(r"`((?:\.cursor|scripts|docs/framework)/[^`\s<>*|]+)`")
        files = [*(ROOT / ".cursor").rglob("*.md"), *(ROOT / ".cursor").rglob("*.mdc"),
                 *(ROOT / "docs" / "framework").glob("*.md")]
        missing = []
        for f in files:
            # Skip speckit templates, the ponytail rule prose, and vendored third-party skills
            # under .cursor/skills/_external (not audited, not versioned; see .gitignore).
            if "speckit" in str(f) or "ponytail.mdc" in f.name or "_external" in f.parts:
                continue
            for p in rx.findall(f.read_text(encoding="utf-8")):
                p = p.rstrip(".,;:)")
                if re.search(r"YYYY|\bN\b|\.\.\.|\{", p):
                    continue
                if not (ROOT / p).exists():
                    missing.append(f"{f.relative_to(ROOT)} -> {p}")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
