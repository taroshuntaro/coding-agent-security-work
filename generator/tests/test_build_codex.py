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

    def test_config_network_with_domains(self):
        parsed = tomllib.loads(build_codex.build_config("L2", ["npm"], ["github.com"], []))
        net = parsed["permissions"]["business-workspace"]["network"]
        self.assertEqual(net, {"enabled": True, "domains": {"github.com": "allow"}})

    def test_config_network_without_domains(self):
        parsed = tomllib.loads(build_codex.build_config("L2", ["npm"], [], []))
        net = parsed["permissions"]["business-workspace"]["network"]
        self.assertEqual(net, {"enabled": False})

    def test_requirements_network_with_domains(self):
        parsed = tomllib.loads(build_codex.build_requirements("L2", ["github.com"], []))
        net = parsed["permissions"]["org-workspace"]["network"]
        self.assertEqual(net, {"enabled": True, "domains": {"github.com": "allow"}})

    def test_requirements_network_without_domains(self):
        parsed = tomllib.loads(build_codex.build_requirements("L2", [], []))
        net = parsed["permissions"]["org-workspace"]["network"]
        self.assertEqual(net, {"enabled": False})

    def test_requirements_org_workspace_protects_repo_metadata(self):
        # docs/10-codex.md 10.5: .devcontainer / .codex / .git は read に落とす
        parsed = tomllib.loads(build_codex.build_requirements("L3", ["github.com"], []))
        roots = parsed["permissions"]["org-workspace"]["filesystem"][":workspace_roots"]
        self.assertEqual(roots, {".devcontainer": "read",
                                 ".codex": "read", ".git": "read"})

    def test_config_domains_enable_network_proxy(self):
        # docs/10 10.4: network.enabled だけではドメイン規則が効かず直接通信になる。
        # features.network_proxy = true でプロキシを起動して許可リストを強制する。
        parsed = tomllib.loads(build_codex.build_config("L2", ["npm"], ["github.com"], []))
        self.assertIs(parsed["features"]["network_proxy"], True)

    def test_config_without_domains_has_no_network_proxy(self):
        parsed = tomllib.loads(build_codex.build_config("L2", ["npm"], [], []))
        self.assertNotIn("features", parsed)

    def test_requirements_domains_enable_managed_network(self):
        # docs/10 10.5: 管理側は [experimental_network] でプロキシを起動し、
        # 管理者の allow 規則だけを有効にする。
        parsed = tomllib.loads(build_codex.build_requirements("L3", ["github.com"], []))
        self.assertEqual(parsed["experimental_network"], {
            "enabled": True,
            "managed_allowed_domains_only": True,
            "domains": {"github.com": "allow"},
        })

    def test_requirements_without_domains_has_no_managed_network(self):
        parsed = tomllib.loads(build_codex.build_requirements("L3", [], []))
        self.assertNotIn("experimental_network", parsed)

    def test_requirements_deny_read_uses_absolute_or_home_paths(self):
        # managed-configuration: deny_read は絶対パスか ~ 始まり（./ 始まりは不可）
        parsed = tomllib.loads(build_codex.build_requirements(
            "L3", [], ["config/secret.yml", "./keys/**", "**/certs/**", "~/.gnupg", "/etc/x"]))
        deny_read = parsed["permissions"]["filesystem"]["deny_read"]
        for entry in deny_read:
            self.assertTrue(entry.startswith(("/", "~")), entry)
        for expected in ["/**/.env", "/**/.env.*", "/**/secrets/**",
                         "/**/config/secret.yml", "/**/keys/**", "/**/certs/**",
                         "~/.gnupg", "/etc/x", "~/.ssh"]:
            self.assertIn(expected, deny_read)

    def test_config_workspace_roots_keep_relative_globs(self):
        # :workspace_roots 配下は各ワークスペースルート相対の glob が公式の書式
        parsed = tomllib.loads(build_codex.build_config("L2", ["npm"], [], ["**/keys/**"]))
        roots = parsed["permissions"]["business-workspace"]["filesystem"][":workspace_roots"]
        self.assertEqual(roots["**/.env"], "deny")
        self.assertEqual(roots["**/keys/**"], "deny")

    def test_config_l1_header_has_no_workspace_premise(self):
        # L1 は :read-only であり extends = ":workspace" を前提としない
        toml = build_codex.build_config("L1", ["npm"], ["github.com"], [])
        self.assertNotIn(':workspace" を前提', toml)

    def test_config_l2_header_notes_workspace_premise(self):
        toml = build_codex.build_config("L2", ["npm"], ["github.com"], [])
        self.assertIn(':workspace" を前提', toml)
