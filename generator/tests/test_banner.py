import unittest
from agentsec import banner

FORBIDDEN = ["privileged", "network_mode: host", "docker.sock", "/:/host"]


class TestBanner(unittest.TestCase):
    def test_banner_is_comment_lines(self):
        for line in banner.banner("L2", ["claude", "codex"]).splitlines():
            self.assertTrue(line.startswith("#"), line)

    def test_banner_mentions_level_and_source_of_truth(self):
        text = banner.banner("L3", ["codex"])
        self.assertIn("L3", text)
        self.assertIn("docs/", text)

    def test_banner_has_no_selfcheck_forbidden_words(self):
        text = banner.banner("L4", ["claude"])
        for needle in FORBIDDEN:
            self.assertNotIn(needle, text)
