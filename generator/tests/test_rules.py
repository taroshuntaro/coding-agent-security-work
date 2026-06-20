import unittest
from agentsec import rules


class TestRules(unittest.TestCase):
    def test_constants_present(self):
        self.assertEqual(rules.LEVELS, ("L1", "L2", "L3", "L4"))
        self.assertIn("git push *", rules.BASE_DENY_COMMANDS)
        self.assertIn("sudo *", rules.BASE_DENY_COMMANDS)
        self.assertIn("./.env", rules.SENSITIVE_READ_PATHS)
        self.assertIn("~/.aws", rules.CREDENTIAL_DIRS)

    def test_level_profile_l1(self):
        p = rules.level_profile("L1")
        self.assertEqual(p["default_mode"], "plan")
        self.assertFalse(p["managed_required"])

    def test_level_profile_l3_requires_managed(self):
        p = rules.level_profile("L3")
        self.assertTrue(p["managed_required"])
        self.assertTrue(p["sandbox_fail_if_unavailable"])
        self.assertEqual(p["web_search"], "cached")

    def test_level_profile_invalid(self):
        with self.assertRaises(ValueError):
            rules.level_profile("L9")
