import unittest
from agentsec import checklist


class TestChecklistExtraRows(unittest.TestCase):
    def test_claude_rows_cover_scope_and_start_mode(self):
        rows = checklist.extra_rows(["claude"])
        self.assertIn("strictAllowlist", rows)
        self.assertIn("defaultMode", rows)

    def test_codex_auto_review_row_only_for_codex(self):
        self.assertIn("auto-review", checklist.extra_rows(["codex"]))
        self.assertNotIn("auto-review", checklist.extra_rows(["claude"]))

    def test_rows_are_markdown_table_rows(self):
        for line in checklist.extra_rows(["claude", "codex"]).splitlines():
            self.assertTrue(line.startswith("| ") and line.endswith(" |"), line)

    def test_no_rows_without_known_products(self):
        self.assertEqual(checklist.extra_rows([]), "")
