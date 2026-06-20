"""Codex の config.toml / requirements.toml を組み立てる。docs/10-codex.md 準拠。"""

from agentsec import rules, render_toml


def _filesystem_deny_paths(extra_deny_paths):
    base = ["**/.env", "**/.env.*", "**/secrets/**"]
    return base + list(extra_deny_paths)


def build_config(level, stacks_keys, allowed_domains, extra_deny_paths):
    prof = rules.level_profile(level)
    workspace_roots = {p: "deny" for p in _filesystem_deny_paths(extra_deny_paths)}
    workspace_roots[".devcontainer"] = "read"

    network = {"enabled": bool(allowed_domains)}
    config = {
        "approval_policy": "on-request",
        "web_search": prof["web_search"],
        "default_permissions": "business-workspace",
        "permissions": {
            "business-workspace": {
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
    }
    if allowed_domains:
        config["permissions"]["business-workspace"]["network"] = {
            "enabled": True,
            "domains": {d: "allow" for d in allowed_domains},
        }
    header = "# ~/.codex/config.toml\n# extends = \":workspace\" を前提とする（適用時に確認）\n"
    return header + render_toml.dumps(config)


def build_requirements(level, allowed_domains, extra_deny_paths):
    prof = rules.level_profile(level)
    req = {
        "allowed_approval_policies": ["untrusted", "on-request"],
        "allowed_web_search_modes": [prof["web_search"]] if prof["web_search"] != "disabled" else ["cached"],
        "allow_remote_control": False,
        "allow_appshots": False,
        "allow_managed_hooks_only": True,
        "default_permissions": "org-workspace",
        "allowed_permission_profiles": {":read-only": True, "org-workspace": True},
        "permissions": {
            "filesystem": {
                "deny_read": _filesystem_deny_paths(extra_deny_paths) + rules.CREDENTIAL_DIRS,
            },
            "org-workspace": {
                "description": "Managed workspace access with sensitive files denied",
                "filesystem": {":root": "deny", ":minimal": "read", "glob_scan_max_depth": 4},
                "network": {"enabled": bool(allowed_domains)},
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
        req["permissions"]["org-workspace"]["network"] = {
            "enabled": True, "domains": {d: "allow" for d in allowed_domains}}
    return "# 組織管理 requirements.toml（team プラン用）\n" + render_toml.dumps(req)
