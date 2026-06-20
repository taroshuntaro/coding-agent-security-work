import unittest
import tomllib
from agentsec import build_codex


class TestBuildCodex(unittest.TestCase):
    def test_config_has_no_full_access_and_cached_search(self):
        toml = build_codex.build_config("L2", ["npm"], ["github.com"], [])
        parsed = tomllib.loads(toml)
        self.assertEqual(parsed["web_search"], "cached")
        self.assertEqual(parsed["approval_policy"], "on-request")

    def test_config_denies_sensitive_paths(self):
        toml = build_codex.build_config("L2", ["npm"], ["github.com"], ["**/keys/**"])
        self.assertIn("**/.env", toml)
        self.assertIn("**/keys/**", toml)

    def test_requirements_excludes_danger_full_access(self):
        toml = build_codex.build_requirements("L3", ["github.com"], [])
        parsed = tomllib.loads(toml)
        self.assertNotIn(":danger-full-access", parsed["allowed_permission_profiles"])
        self.assertEqual(parsed["allowed_web_search_modes"], ["cached"])

    def test_requirements_forbids_git_push(self):
        toml = build_codex.build_requirements("L3", ["github.com"], [])
        self.assertIn('decision = "forbidden"', toml)
        self.assertIn("git", toml)

    def test_config_l1_is_read_only(self):
        toml = build_codex.build_config("L1", ["npm"], ["github.com"], [])
        parsed = tomllib.loads(toml)
        self.assertEqual(parsed["default_permissions"], ":read-only")
        self.assertEqual(parsed["approval_policy"], "on-request")
        self.assertNotIn("business-workspace", parsed.get("permissions", {}))

    def test_config_l2_business_workspace_extends(self):
        toml = build_codex.build_config("L2", ["npm"], ["github.com"], [])
        parsed = tomllib.loads(toml)
        self.assertEqual(parsed["permissions"]["business-workspace"]["extends"], ":workspace")

    def test_requirements_org_workspace_extends(self):
        toml = build_codex.build_requirements("L2", ["github.com"], [])
        parsed = tomllib.loads(toml)
        self.assertEqual(parsed["permissions"]["org-workspace"]["extends"], ":workspace")
