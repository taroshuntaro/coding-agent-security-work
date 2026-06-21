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


class TestPlacementGuide(unittest.TestCase):
    def test_managed_row_and_precedence_when_managed_present(self):
        out = readme.placement_guide({"claude-code/managed-settings.json"})
        self.assertIn("リポジトリ外", out)
        self.assertIn("管理 > プロジェクト > ユーザー", out)

    def test_r6_caveat_always_present(self):
        out = readme.placement_guide({"codex/.codex/config.toml"})
        self.assertIn("R6", out)
        self.assertIn("強制ポリシーとみなさない", out)

    def test_managed_row_absent_without_managed_files(self):
        out = readme.placement_guide({"claude-code/.claude/settings.json"})
        self.assertNotIn("OS 管理パス", out)
