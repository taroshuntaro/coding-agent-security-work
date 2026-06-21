import unittest
from agentsec import readme


class TestReadme(unittest.TestCase):
    def test_guide_lists_only_present_files(self):
        keys = {"claude-code/.claude/settings.json", "codex/.codex/config.toml"}
        text = readme.artifact_guide(keys)
        self.assertIn("settings.json", text)
        self.assertIn("config.toml", text)
        self.assertNotIn("managed-settings.json", text)

    def test_apply_steps_omit_managed_when_absent(self):
        keys = {"claude-code/.claude/settings.json"}
        text = readme.apply_steps(keys)
        self.assertNotIn("managed-settings.json", text)

    def test_apply_steps_include_managed_when_present(self):
        keys = {"claude-code/.claude/settings.json", "claude-code/managed-settings.json"}
        text = readme.apply_steps(keys)
        self.assertIn("managed-settings.json", text)
