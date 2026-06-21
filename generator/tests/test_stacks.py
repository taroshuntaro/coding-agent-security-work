import unittest
from agentsec import stacks


class TestStacks(unittest.TestCase):
    def test_npm_commands(self):
        result = stacks.commands_for(["npm"])
        self.assertIn("Bash(npm run test *)", result["allow"])
        self.assertIn("Bash(npm install *)", result["ask"])

    def test_multiple_stacks_merge_and_dedup(self):
        result = stacks.commands_for(["npm", "npm", "maven"])
        # 重複なし・ソート済み
        self.assertEqual(result["allow"], sorted(set(result["allow"])))
        self.assertTrue(any("mvn" in c for c in result["allow"]))

    def test_unknown_stack_raises(self):
        with self.assertRaises(ValueError):
            stacks.commands_for(["cobol"])

    def test_known_contains_all_stack_keys(self):
        self.assertEqual(stacks.KNOWN, frozenset(stacks.STACKS))

    def test_unknown_keys_returns_only_unknown_in_order(self):
        self.assertEqual(stacks.unknown_keys(["npm", "rust", "pip", "ruby"]), ["rust", "ruby"])

    def test_unknown_keys_empty_when_all_known(self):
        self.assertEqual(stacks.unknown_keys(["npm", "pip"]), [])
