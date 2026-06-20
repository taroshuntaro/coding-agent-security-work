import unittest
import tempfile
import os
import json
from agentsec import selfcheck


def _write(d, rel, text):
    path = os.path.join(d, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class TestSelfcheck(unittest.TestCase):
    def test_clean_settings_pass(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "claude-code/.claude/settings.json", json.dumps({
                "permissions": {"deny": ["Read(./.env)", "Bash(git push *)", "Bash(sudo *)"]},
                "sandbox": {"autoAllowBashIfSandboxed": False},
            }))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0)

    def test_missing_git_push_deny_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "claude-code/.claude/settings.json", json.dumps({
                "permissions": {"deny": ["Read(./.env)"]},
                "sandbox": {"autoAllowBashIfSandboxed": False},
            }))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("git push" in m for m in msgs))

    def test_compose_docker_socket_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "docker-compose.yml",
                   "services:\n  dev:\n    volumes:\n      - /var/run/docker.sock:/var/run/docker.sock\n")
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("docker.sock" in m for m in msgs))

    def test_compose_comment_with_forbidden_token_passes(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "docker-compose.yml",
                   "# privileged mode and docker.sock are intentionally not used\n"
                   "services:\n  dev:\n    image: node:20\n")
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)

    def test_recorded_redline_still_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "generation-profile.json", json.dumps({
                "deviations": [{"type": "redline", "rule_ref": "00 R3"}]}))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("redline" in m.lower() for m in msgs))
