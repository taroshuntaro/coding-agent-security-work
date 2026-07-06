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

    def test_npm_domains(self):
        self.assertEqual(stacks.domains_for(["npm"]), ["registry.npmjs.org"])

    def test_multiple_stack_domains_merge_sorted_dedup(self):
        result = stacks.domains_for(["maven", "gradle"])
        # repo.maven.apache.org は重複排除され1回だけ
        self.assertEqual(result,
                         ["plugins.gradle.org", "repo.maven.apache.org"])

    def test_empty_stacks_empty_domains(self):
        self.assertEqual(stacks.domains_for([]), [])

    def test_unknown_stack_domains_raises(self):
        with self.assertRaises(ValueError):
            stacks.domains_for(["cobol"])

    def test_every_stack_has_domains_key(self):
        for key, spec in stacks.STACKS.items():
            self.assertIn("domains", spec, key)
            self.assertTrue(spec["domains"], key)
