import unittest
import tempfile
import os
import json
from pathlib import Path
from agentsec import orchestrate, selfcheck, deviation


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

    def test_commentable_files_have_banner(self):
        with tempfile.TemporaryDirectory() as d:
            files = orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            for rel in ("codex/.codex/config.toml", "docker-compose.yml", "Dockerfile"):
                text = Path(files[rel]).read_text(encoding="utf-8")
                self.assertIn("自動生成: coding-agent-security", text)

    def test_json_files_have_no_banner(self):
        with tempfile.TemporaryDirectory() as d:
            files = orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            text = Path(files["claude-code/.claude/settings.json"]).read_text(encoding="utf-8")
            self.assertNotIn("自動生成: coding-agent-security", text)

    def test_readme_lists_generated_artifacts_and_uses_python3(self):
        with tempfile.TemporaryDirectory() as d:
            files = orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            text = Path(files["README.md"]).read_text(encoding="utf-8")
            self.assertIn("config.toml", text)
            self.assertIn("python3 acceptance/selfcheck.py", text)

    def test_readme_omits_managed_for_personal_plan(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._profile()
            p["plan"] = "personal"
            files = orchestrate.generate(p, d, [], "node:20-bookworm-slim")
            text = Path(files["README.md"]).read_text(encoding="utf-8")
            self.assertNotIn("managed-settings.json", text)

    def test_redline_override_records_deviation_and_selfcheck_fails(self):
        dev = deviation.make(
            "redline", "00 R3", "bypass used", "no bypass",
            reason="legacy", approver="alice", date="2026-06-21")
        profile = {"products": ["claude", "codex"], "level": "L2", "plan": "team",
                   "stacks": ["npm"], "allowed_domains": ["github.com"],
                   "extra_deny_paths": [], "use_container": True,
                   "use_full_access": False, "share_docker_socket": False,
                   "network_host": False, "direct_push": False}
        with tempfile.TemporaryDirectory() as d:
            files = orchestrate.generate(profile, d, [dev], "node:20-bookworm-slim")
            # generation-profile.json contains the redline deviation
            gen_profile_path = files["generation-profile.json"]
            gen_profile = json.loads(Path(gen_profile_path).read_text(encoding="utf-8"))
            self.assertTrue(len(gen_profile["deviations"]) > 0)
            self.assertEqual(gen_profile["deviations"][0]["type"], "redline")
            # POLICY-SHEET.md contains the approver
            policy_path = files["POLICY-SHEET.md"]
            policy_text = Path(policy_path).read_text(encoding="utf-8")
            self.assertIn("alice", policy_text)
            # selfcheck returns exit code 2 for a recorded redline
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2, msgs)

    def test_output_has_files_false_for_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(orchestrate.output_has_files(d))

    def test_output_has_files_true_after_generate(self):
        with tempfile.TemporaryDirectory() as d:
            orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            self.assertTrue(orchestrate.output_has_files(d))
