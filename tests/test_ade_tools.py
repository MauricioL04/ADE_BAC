"""Unit tests for the ADE tooling (scripts/ade/verify.py and guard.py)."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "ade" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


verify = load("verify")
guard = load("guard")


class GuardTests(unittest.TestCase):
    def assertAsk(self, cmd):
        self.assertEqual(guard.evaluate(cmd)[0], "ask", cmd)

    def assertAllow(self, cmd):
        self.assertEqual(guard.evaluate(cmd)[0], "allow", cmd)

    def test_destructive_commands_require_approval(self):
        for cmd in [
            "git push --force origin main",
            "git push -f",
            "git reset --hard HEAD~3",
            "git commit --no-verify -m x",
            "rm -rf build",
            "Remove-Item C:\\data -Recurse -Force",
            "sqlplus u/p@db <<< 'DROP TABLE users;'",
            "psql -c \"TRUNCATE TABLE orders\"",
            "psql -c \"DELETE FROM orders\"",
            "terraform apply",
            "kubectl apply -f prod.yaml",
            "type .env",
            "git push origin main",
            "git push origin master",
            "git push origin HEAD:main",
            "git push origin HEAD:refs/heads/master",
            "git push -u origin main",
        ]:
            self.assertAsk(cmd)

    def test_push_to_main_variants_are_caught_with_the_right_category(self):
        for cmd in ['git push origin "main"', "git push origin 'master'", "git -C repo push origin main",
                    "git -c k=v push origin main", "git --no-pager push origin main", "git push origin main;",
                    "git push origin main&&echo ok", "git push --force-with-lease origin main"]:
            self.assertEqual(guard.evaluate(cmd), ("ask", "git: push to main/master"), cmd)
        self.assertEqual(guard.evaluate("git push origin +main")[0], "ask")

    def test_main_after_a_separator_is_not_a_push_to_main(self):
        for cmd in ["git push origin feature && git checkout main", "git push origin feature; git merge main",
                    "git push origin feature/main", "git push origin feature/main-fix"]:
            self.assertAllow(cmd)

    def test_push_with_variable_ref_requires_approval(self):
        for cmd in ["git push origin $branch", "git push origin ${branch}", "git push origin %BRANCH%",
                    "git push origin !BRANCH!"]:
            self.assertEqual(guard.evaluate(cmd), ("ask", "git: push with variable ref"), cmd)

    def test_safe_commands_pass(self):
        for cmd in [
            "git status",
            "git push --force-with-lease origin feature",
            "git push origin feature",
            "git push origin feature/main-fix",
            "git push origin domain",
            "git pull origin main",
            "python scripts/ade/verify.py",
            "psql -c \"DELETE FROM orders WHERE id = 1\"",
            "cat .env.example",
            "npm test",
            "ls",
        ]:
            self.assertAllow(cmd)


class DetectTests(unittest.TestCase):
    def test_node_scripts_are_detected_not_invented(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "package.json").write_text(json.dumps({"scripts": {"test": "x", "lint": "y"}}))
            plan = verify.detect(root)
            self.assertIn("node", plan.stack)
            self.assertEqual(plan.stages["unit"].cmd, ["npm", "run", "--silent", "test"])
            self.assertEqual(plan.stages["lint"].cmd, ["npm", "run", "--silent", "lint"])
            self.assertIsNone(plan.stages["build"].cmd)
            self.assertIsNone(plan.stages["typecheck"].cmd)

    def test_empty_repo_detects_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            plan = verify.detect(Path(d))
            self.assertEqual(plan.stack, [])
            self.assertTrue(all(s.cmd is None for s in plan.stages.values()))

    def test_skip_is_never_reported_as_pass(self):
        with tempfile.TemporaryDirectory() as d:
            plan = verify.detect(Path(d))
            report = verify.render(plan, [], "SKIP")
            self.assertNotIn("PASS", report.replace("Secret Scan:\nPASS", ""))


class JsonOutputTests(unittest.TestCase):
    def test_to_dict_is_machine_readable_and_distinguishes_skip(self):
        with tempfile.TemporaryDirectory() as d:
            plan = verify.detect(Path(d))
            data = verify.to_dict(plan, [], "SKIP")
            self.assertEqual(data["stack"], [])
            self.assertEqual(data["stages"]["build"], "SKIP")
            self.assertEqual(data["secrets"], {"status": "PASS", "findings": []})
            self.assertTrue(data["ok"])
            json.dumps(data)  # must be serializable

    def test_failed_secret_scan_makes_ok_false(self):
        with tempfile.TemporaryDirectory() as d:
            plan = verify.detect(Path(d))
            data = verify.to_dict(plan, ["x.txt:1: AWS access key id"], "SKIP")
            self.assertFalse(data["ok"])
            self.assertEqual(data["secrets"]["status"], "FAIL")

    def test_cli_json_flag_prints_only_json(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.py").write_text("x = 1\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = verify.main(["--root", d, "--json"])
            data = json.loads(buf.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(data["stages"]["build"], "PASS")


class RunStageTests(unittest.TestCase):
    def test_hanging_command_fails_instead_of_blocking(self):
        stage = verify.Stage("unit", cmd=[sys.executable, "-c", "import time; time.sleep(30)"])
        verify.run_stage(stage, ROOT, timeout=1)
        self.assertEqual(stage.status, verify.FAIL)
        self.assertIn("timed out", stage.output)

    def test_missing_tool_fails_and_no_command_skips(self):
        missing = verify.Stage("build", cmd=["definitely-not-a-real-tool-xyz"])
        verify.run_stage(missing, ROOT)
        self.assertEqual(missing.status, verify.FAIL)
        none = verify.Stage("lint")
        verify.run_stage(none, ROOT)
        self.assertEqual(none.status, verify.SKIP)


class SecretScanTests(unittest.TestCase):
    def test_detects_aws_key_and_env_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fake_key = "AKIA" + "ABCDEFGHIJKLMNOP"  # built at runtime: no literal secret in repo
            (root / "config.txt").write_text(f"key = {fake_key}\n")
            (root / ".env").write_text("X=1\n")
            found = verify.scan_secrets(root)
            self.assertTrue(any("AWS access key" in f for f in found))
            self.assertTrue(any(".env" in f for f in found))

    def test_clean_repo_and_allow_marker(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.py").write_text("print('hi')\n")
            (root / "b.py").write_text("password = 'not-a-real-secret-value'  # ade:allow-secret\n")
            (root / ".env.example").write_text("API_KEY=\n")
            self.assertEqual(verify.scan_secrets(root), [])


if __name__ == "__main__":
    unittest.main()
