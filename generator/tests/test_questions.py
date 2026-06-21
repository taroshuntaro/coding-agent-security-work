import unittest
from agentsec import questions, rules


class TestQuestions(unittest.TestCase):
    def _q(self, key):
        q = next((q for q in questions.QUESTIONS if q["key"] == key), None)
        self.assertIsNotNone(q, f"no question with key={key!r}")
        return q

    def test_every_question_has_help_and_detail(self):
        for q in questions.QUESTIONS:
            self.assertTrue(q["help_line"].strip(), q["key"])
            self.assertTrue(q["detail"].strip(), q["key"])
            self.assertIn(q["type"], ("yesno", "choice", "csv"), q["key"])

    def test_level_default_is_l2(self):
        self.assertEqual(self._q("level")["default"], "L2")

    def test_redline_questions_default_to_no(self):
        for key in ("use_full_access", "share_docker_socket", "network_host", "direct_push"):
            self.assertEqual(self._q(key)["default"], "n", key)

    def test_render_prompt_shows_default_and_help(self):
        text = questions.render_prompt(self._q("level"))
        self.assertIn("L2", text)
        self.assertIn("?", text)

    def test_resolve_question_mark_returns_help(self):
        self.assertEqual(questions.resolve_answer(self._q("level"), "?"), ("help", None))

    def test_resolve_empty_uses_default(self):
        self.assertEqual(questions.resolve_answer(self._q("level"), ""), ("ok", "L2"))

    def test_resolve_yesno_to_bool(self):
        self.assertEqual(questions.resolve_answer(self._q("use_full_access"), "y"), ("ok", True))
        self.assertEqual(questions.resolve_answer(self._q("use_full_access"), ""), ("ok", False))

    def test_resolve_choice_validates(self):
        status, msg = questions.resolve_answer(self._q("level"), "L9")
        self.assertEqual(status, "error")
        self.assertIn("L1", msg)

    def test_resolve_csv_splits_and_trims(self):
        self.assertEqual(
            questions.resolve_answer(self._q("stacks"), " npm , pip "),
            ("ok", ["npm", "pip"]))

    def test_resolve_csv_empty_stacks_is_empty_list(self):
        self.assertEqual(questions.resolve_answer(self._q("stacks"), ""), ("ok", []))

    def test_resolve_csv_empty_domains_uses_default(self):
        self.assertEqual(
            questions.resolve_answer(self._q("allowed_domains"), ""),
            ("ok", list(rules.DEFAULT_ALLOWED_DOMAINS)))

    def test_resolve_csv_drops_empty_segments(self):
        self.assertEqual(
            questions.resolve_answer(self._q("stacks"), "npm,,pip"),
            ("ok", ["npm", "pip"]))

    def test_resolve_invalid_yesno_returns_error(self):
        status, msg = questions.resolve_answer(self._q("use_full_access"), "x")
        self.assertEqual(status, "error")
        self.assertIn("y", msg)
