"""Codex の config.toml / requirements.toml を組み立てる。docs/10-codex.md 準拠。"""

from agentsec import rules, render_toml


def _filesystem_deny_paths(extra_deny_paths):
    base = ["**/.env", "**/.env.*", "**/secrets/**"]
    return base + list(extra_deny_paths)


def _deny_read_pattern(path):
    """requirements.toml の deny_read は絶対パスか ~ 始まりで書く（./ 始まりは不可。
    docs/10 10.5）。ワークスペース相対の glob はどの階層でも一致する絶対 glob へ直す。"""
    if path.startswith(("/", "~")):
        return path
    if path.startswith("./"):
        path = path[2:]
    if path.startswith("**/"):
        return "/" + path
    return "/**/" + path


def build_config(level, stacks_keys, allowed_domains, extra_deny_paths):
    prof = rules.level_profile(level)
    header = "# ~/.codex/config.toml\n"

    if level == "L1":
        config = {
            "approval_policy": "on-request",
            "web_search": prof["web_search"],
            "default_permissions": ":read-only",
        }
        return header + render_toml.dumps(config)

    header += "# extends = \":workspace\" を前提とする（適用時に確認）\n"
    workspace_roots = {p: "deny" for p in _filesystem_deny_paths(extra_deny_paths)}
    workspace_roots[".devcontainer"] = "read"

    network = {"enabled": bool(allowed_domains)}
    if allowed_domains:
        network["domains"] = {d: "allow" for d in allowed_domains}
    config = {
        "approval_policy": "on-request",
        "web_search": prof["web_search"],
        "default_permissions": "business-workspace",
    }
    if allowed_domains:
        # network.enabled はプロキシを起動しない。プロキシが無いとドメイン規則は
        # 適用されず、コマンドは無制限に直接通信できる（docs/10 10.4）。
        config["features"] = {"network_proxy": True}
    config.update({
        "permissions": {
            "business-workspace": {
                "extends": ":workspace",
                "description": "Workspace editing with restricted network",
                "filesystem": {
                    ":root": "deny",
                    ":minimal": "read",
                    "glob_scan_max_depth": 4,
                    ":workspace_roots": workspace_roots,
                },
                "network": network,
            }
        },
    })
    return header + render_toml.dumps(config)


def build_requirements(level, allowed_domains, extra_deny_paths):
    prof = rules.level_profile(level)
    org_network = {"enabled": bool(allowed_domains)}
    if allowed_domains:
        org_network["domains"] = {d: "allow" for d in allowed_domains}
    req = {
        "allowed_approval_policies": ["untrusted", "on-request"],
        # disabled は常に許可されるため、L4 の config(web_search=disabled) と
        # この allowed_web_search_modes(=["cached"]) は矛盾しない（docs 10.3.2/10.5）。
        "allowed_web_search_modes": [prof["web_search"]] if prof["web_search"] != "disabled" else ["cached"],
        "allow_remote_control": False,
        "allow_appshots": False,
        "allow_managed_hooks_only": True,
        "default_permissions": "org-workspace",
        "allowed_permission_profiles": {":read-only": True, "org-workspace": True},
        "permissions": {
            "filesystem": {
                "deny_read": [_deny_read_pattern(p) for p in _filesystem_deny_paths(extra_deny_paths)]
                + rules.CREDENTIAL_PATHS,
            },
            "org-workspace": {
                "extends": ":workspace",
                "description": "Managed workspace access with sensitive files denied",
                "filesystem": {
                    ":root": "deny", ":minimal": "read", "glob_scan_max_depth": 4,
                    # docs/10-codex.md 10.5: リポジトリメタデータは read に落とす
                    ":workspace_roots": {".devcontainer": "read",
                                         ".codex": "read", ".git": "read"},
                },
                "network": org_network,
            },
        },
        "rules": {
            "prefix_rules": [
                {"pattern": [{"token": "git"}, {"token": "push"}], "decision": "forbidden",
                 "justification": "Remote repository mutation is performed outside the agent session."},
                {"pattern": [{"token": "sudo"}], "decision": "forbidden",
                 "justification": "Privilege escalation is not allowed."},
                {"pattern": [{"token": "terraform"}, {"any_of": ["apply", "destroy"]}], "decision": "forbidden",
                 "justification": "Infrastructure changes require an approved pipeline."},
            ]
        },
    }
    if allowed_domains:
        # 管理側でプロキシを起動し、管理者の allow 規則だけを有効にする（docs/10 10.5）。
        # 利用者の features.network_proxy に依存しない。
        req["experimental_network"] = {
            "enabled": True,
            "managed_allowed_domains_only": True,
            "domains": {d: "allow" for d in allowed_domains},
        }
    return "# 組織管理 requirements.toml（team プラン用）\n" + render_toml.dumps(req)
