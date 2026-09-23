import unittest
from agentsec import build_claude


class TestBuildClaude(unittest.TestCase):
    def test_settings_denies_credentials_and_commands(self):
        s = build_claude.build_settings("L2", ["npm"], ["github.com"], [])
        self.assertIn("Read(./.env)", s["permissions"]["deny"])
        self.assertIn("Bash(git push *)", s["permissions"]["deny"])
        self.assertIn("~/.aws", s["sandbox"]["filesystem"]["denyRead"])

    def test_settings_allow_includes_stack_commands(self):
        s = build_claude.build_settings("L2", ["npm"], ["github.com"], [])
        self.assertIn("Bash(npm run test *)", s["permissions"]["allow"])

    def test_managed_disables_bypass_and_forces_sandbox(self):
        m = build_claude.build_managed_settings("L3", ["maven"], ["github.com"], [], [])
        self.assertEqual(m["permissions"]["disableBypassPermissionsMode"], "disable")
        self.assertTrue(m["sandbox"]["failIfUnavailable"])
        self.assertTrue(m["sandbox"]["filesystem"]["allowManagedReadPathsOnly"])
        self.assertTrue(m["allowManagedDomainsOnly"]
                        if "allowManagedDomainsOnly" in m
                        else m["sandbox"]["network"]["allowManagedDomainsOnly"])

    def test_managed_settings_omits_required_version_by_default(self):
        s = build_claude.build_managed_settings("L3", ["npm"], ["github.com"], [], [])
        self.assertNotIn("requiredMinimumVersion", s)

    def test_managed_settings_includes_required_version_when_given(self):
        s = build_claude.build_managed_settings(
            "L3", ["npm"], ["github.com"], [], [], claude_min_version="2.1.163")
        self.assertEqual(s["requiredMinimumVersion"], "2.1.163")

    def test_settings_allow_readonly_git_commands(self):
        s = build_claude.build_settings("L2", [], ["github.com"], [])
        for cmd in ("Bash(git status)", "Bash(git diff *)", "Bash(git log *)"):
            self.assertIn(cmd, s["permissions"]["allow"])

    def test_managed_allow_readonly_git_commands(self):
        m = build_claude.build_managed_settings("L3", [], ["github.com"], [], [])
        for cmd in ("Bash(git status)", "Bash(git diff *)", "Bash(git log *)"):
            self.assertIn(cmd, m["permissions"]["allow"])

    def test_settings_asks_websearch(self):
        # docs/11-claude-code.md 11.4: ask に WebSearch を置く
        s = build_claude.build_settings("L2", ["npm"], ["github.com"], [])
        self.assertIn("WebSearch", s["permissions"]["ask"])

    def test_managed_asks_git_commit(self):
        # docs/11-claude-code.md 11.5: ask に Bash(git commit *) を含む
        m = build_claude.build_managed_settings("L3", ["npm"], ["github.com"], [], [])
        self.assertIn("Bash(git commit *)", m["permissions"]["ask"])

    def test_settings_network_omits_strict_allowlist(self):
        # docs/11 11.4: strictAllowlist は user/managed/--settings でのみ有効で、
        # リポジトリの .claude/settings.json に置いても効かない（2026-09-21 確認）。
        # 効かないキーを生成すると「設定した」と誤認させるため出力しない。
        s = build_claude.build_settings("L2", ["npm"], ["github.com"], [])
        self.assertNotIn("strictAllowlist", s["sandbox"]["network"])

    def test_managed_network_strict_allowlist(self):
        m = build_claude.build_managed_settings("L3", ["npm"], ["github.com"], [], [])
        self.assertIs(m["sandbox"]["network"]["strictAllowlist"], True)

    def test_managed_denies_websearch_not_ask(self):
        # managed では WebSearch は deny（11.5）。ask に重複させない
        m = build_claude.build_managed_settings("L3", ["npm"], ["github.com"], [], [])
        self.assertIn("WebSearch", m["permissions"]["deny"])
        self.assertNotIn("WebSearch", m["permissions"]["ask"])

    def test_managed_emits_both_artifact_keys(self):
        # docs/11 11.5: enableArtifact は v2.1.196 以降でのみ認識される。
        # それ未満のクライアントでもロックが外れないよう、公式が同等と認める
        # 旧キー disableArtifact: true も併記する（新キーが正・旧キーは後方互換）。
        m = build_claude.build_managed_settings("L3", ["npm"], ["github.com"], [], [])
        self.assertIs(m["enableArtifact"], False)
        self.assertIs(m["disableArtifact"], True)

    def test_managed_locks_cross_session_messaging(self):
        # docs/11 11.11: 機密案件（L3+）は受信を refuse、他マシンへの送信は承認必須
        m = build_claude.build_managed_settings("L3", ["npm"], ["github.com"], [], [])
        self.assertEqual(m["crossSessionInbound"], "refuse")
        self.assertIs(m["isolatePeerMachines"], True)
