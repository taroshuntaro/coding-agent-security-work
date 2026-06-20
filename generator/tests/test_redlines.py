import unittest
from agentsec import redlines, deviation


class TestRedlines(unittest.TestCase):
    def test_l3_personal_is_redline(self):
        devs = redlines.check_inputs("L3", "personal", False, False, False, False)
        refs = [d["rule_ref"] for d in devs]
        self.assertIn("00 R3/R6", refs)
        self.assertTrue(all(d["type"] == "redline" for d in devs))

    def test_full_access_is_redline(self):
        devs = redlines.check_inputs("L2", "team", True, False, False, False)
        self.assertTrue(any("R3" in d["rule_ref"] for d in devs))

    def test_clean_inputs_no_redline(self):
        devs = redlines.check_inputs("L2", "team", False, False, False, False)
        self.assertEqual(devs, [])

    def test_has_blocking(self):
        devs = redlines.check_inputs("L2", "team", True, False, False, False)
        self.assertTrue(redlines.has_blocking(devs, override=False))
        self.assertFalse(redlines.has_blocking(devs, override=True))

    def test_deviation_make(self):
        d = deviation.make("recommendation", "11.4", "wide domains", "narrow list",
                           reason="legacy CI", approver="alice", date="2026-06-21")
        self.assertEqual(d["type"], "recommendation")
        self.assertEqual(d["approver"], "alice")
