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

    def test_apply_steps_note_user_scope_keys_for_claude(self):
        # strictAllowlist 等は project settings で効かないため user settings への配置を案内
        keys = {"claude-code/.claude/settings.json"}
        text = readme.apply_steps(keys)
        self.assertIn("strictAllowlist", text)
        self.assertIn("~/.claude/settings.json", text)

    def test_apply_steps_route_default_mode_to_user_scope(self):
        # VS Code 拡張はプロジェクト設定を開始モードの決定に使わないため、
        # defaultMode も ~/.claude/settings.json へ置くよう案内する（docs/11 11.2）。
        # 「確認せよ」だけでは、拡張利用時に auto mode で始まる穴が残る。
        text = readme.apply_steps({"claude-code/.claude/settings.json"})
        default_mode_step = [ln for ln in text.splitlines() if "defaultMode" in ln]
        self.assertEqual(len(default_mode_step), 1)
        step = default_mode_step[0]
        self.assertIn("VS Code", step)
        self.assertIn("~/.claude/settings.json", step)
        self.assertIn("にも置く", step)

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

    def test_monorepo_note_present_for_local_layer(self):
        out = readme.placement_guide({"claude-code/.claude/settings.json"})
        self.assertIn("モノレポ", out)
        self.assertIn("共通", out)
