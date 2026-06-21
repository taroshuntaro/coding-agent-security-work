import unittest
from agentsec import summary


class TestSummary(unittest.TestCase):
    def _profile(self):
        return {"products": ["claude", "codex"], "level": "L2", "plan": "team",
                "stacks": ["npm"], "allowed_domains": ["github.com"],
                "extra_deny_paths": [], "use_container": True,
                "use_full_access": False, "share_docker_socket": False,
                "network_host": False, "direct_push": False}

    def test_summary_contains_core_fields(self):
        text = summary.format_summary(self._profile())
        self.assertIn("L2", text)
        self.assertIn("team", text)
        self.assertIn("claude", text)
        self.assertIn("npm", text)
        self.assertIn("github.com", text)

    def test_summary_shows_none_for_empty_lists(self):
        p = self._profile()
        p["stacks"] = []
        p["extra_deny_paths"] = []
        text = summary.format_summary(p)
        self.assertIn("なし", text)

    def test_summary_reports_redline_answers(self):
        p = self._profile()
        p["network_host"] = True
        text = summary.format_summary(p)
        self.assertIn("ホストネットワーク", text)
        self.assertIn("はい", text)
