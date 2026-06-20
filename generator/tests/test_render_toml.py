import unittest
from agentsec import render_toml as rt


class TestTomlEmitter(unittest.TestCase):
    def test_scalars(self):
        out = rt.dumps({"approval_policy": "on-request", "enabled": False, "depth": 4})
        self.assertIn('approval_policy = "on-request"', out)
        self.assertIn("enabled = false", out)
        self.assertIn("depth = 4", out)

    def test_string_array(self):
        out = rt.dumps({"allowed_web_search_modes": ["cached"]})
        self.assertIn('allowed_web_search_modes = ["cached"]', out)

    def test_section(self):
        out = rt.dumps({"permissions": {"org": {"description": "x"}}})
        self.assertIn("[permissions.org]", out)
        self.assertIn('description = "x"', out)

    def test_array_of_inline_tables(self):
        data = {"rules": {"prefix_rules": [
            {"pattern": [{"token": "git"}, {"token": "push"}],
             "decision": "forbidden"},
        ]}}
        out = rt.dumps(data)
        self.assertIn("[rules]", out)
        self.assertIn('pattern = [{token = "git"}, {token = "push"}]', out)
        self.assertIn('decision = "forbidden"', out)

    def test_roundtrip_parseable(self):
        import tomllib
        data = {"a": "b", "section": {"c": [1, 2], "d": True}}
        parsed = tomllib.loads(rt.dumps(data))
        self.assertEqual(parsed["a"], "b")
        self.assertEqual(parsed["section"]["c"], [1, 2])
        self.assertTrue(parsed["section"]["d"])

    def test_quoted_key_at_top_level(self):
        import tomllib
        # Test that a key needing quoting at the top level is quoted
        data = {"x": {"**/.env": "deny"}}
        out = rt.dumps(data)
        self.assertIn('"**/.env" = "deny"', out)
        # Verify it parses and round-trips correctly
        parsed = tomllib.loads(out)
        self.assertEqual(parsed["x"]["**/.env"], "deny")

    def test_quoted_key_in_nested_section(self):
        import tomllib
        # Test that a key needing quoting in a nested section path is escaped properly
        data = {"permissions": {":workspace_roots": {"**/.env": "deny"}}}
        out = rt.dumps(data)
        # The nested key :workspace_roots should be quoted in the section header
        self.assertIn('[permissions.":workspace_roots"]', out)
        self.assertIn('"**/.env" = "deny"', out)
        # Verify it parses and round-trips correctly
        parsed = tomllib.loads(out)
        self.assertEqual(parsed["permissions"][":workspace_roots"]["**/.env"], "deny")
