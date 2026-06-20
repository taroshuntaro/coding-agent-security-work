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
