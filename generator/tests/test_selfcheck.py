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


class TestCodexConfig(unittest.TestCase):
    _L2 = (
        'approval_policy = "on-request"\n'
        'web_search = "cached"\n'
        'default_permissions = "business-workspace"\n'
        '[permissions.business-workspace]\n'
        'extends = ":workspace"\n'
        '[permissions.business-workspace.filesystem.":workspace_roots"]\n'
        '"**/.env" = "deny"\n'
        '".devcontainer" = "read"\n'
    )

    def test_clean_l2_config_passes(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml", self._L2)
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)

    def test_danger_full_access_default_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'approval_policy = "on-request"\n'
                   'default_permissions = ":danger-full-access"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("R3" in m for m in msgs))

    def test_danger_full_access_extends_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'approval_policy = "on-request"\n'
                   'default_permissions = "x"\n'
                   '[permissions.x]\n'
                   'extends = ":danger-full-access"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("R3" in m for m in msgs))

    def test_approval_never_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'approval_policy = "never"\n'
                   'default_permissions = ":read-only"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("10.8" in m for m in msgs))

    def test_workspace_write_missing_env_deny_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'default_permissions = "business-workspace"\n'
                   '[permissions.business-workspace]\n'
                   'extends = ":workspace"\n'
                   '[permissions.business-workspace.filesystem.":workspace_roots"]\n'
                   '".devcontainer" = "read"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("R2" in m for m in msgs))

    def test_l1_read_only_skips_env_check(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'approval_policy = "on-request"\n'
                   'web_search = "cached"\n'
                   'default_permissions = ":read-only"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)
