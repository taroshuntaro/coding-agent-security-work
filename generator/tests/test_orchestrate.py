import unittest
import tempfile
import os
import json
from agentsec import orchestrate, selfcheck


class TestOrchestrate(unittest.TestCase):
    def _profile(self):
        return {"products": ["claude", "codex"], "level": "L2", "plan": "team",
                "stacks": ["npm"], "allowed_domains": ["github.com"],
                "extra_deny_paths": [], "use_container": True}

    def test_generates_expected_files(self):
        with tempfile.TemporaryDirectory() as d:
            files = orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            self.assertIn("claude-code/.claude/settings.json", files)
            self.assertNotIn("claude-code/managed-settings.json", files)
            self.assertIn("codex/.codex/config.toml", files)
            self.assertIn("docker-compose.yml", files)
            self.assertIn("generation-profile.json", files)
            self.assertTrue(os.path.exists(files["generation-profile.json"]))

    def test_generated_output_passes_selfcheck(self):
        with tempfile.TemporaryDirectory() as d:
            orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)

    def test_personal_plan_skips_managed(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._profile()
            p["plan"] = "personal"
            p["level"] = "L2"
            files = orchestrate.generate(p, d, [], "node:20-bookworm-slim")
            self.assertNotIn("claude-code/managed-settings.json", files)

    def test_l3_team_generates_managed_and_passes_selfcheck(self):
        with tempfile.TemporaryDirectory() as d:
            p = {"products": ["claude", "codex"], "level": "L3", "plan": "team",
                 "stacks": ["npm"], "allowed_domains": ["github.com"],
                 "extra_deny_paths": [], "use_container": True}
            files = orchestrate.generate(p, d, [], "node:20-bookworm-slim")
            self.assertIn("claude-code/managed-settings.json", files)
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)
