"""Claude Code の settings.json / managed-settings.json を組み立てる。docs/11-claude-code.md 準拠。"""

from agentsec import rules, stacks

SCHEMA = "https://json.schemastore.org/claude-code-settings.json"


def _deny_reads(extra_deny_paths):
    return [f"Read({p})" for p in rules.SENSITIVE_READ_PATHS] + \
           [f"Read({p})" for p in extra_deny_paths]


def build_settings(level, stacks_keys, allowed_domains, extra_deny_paths):
    prof = rules.level_profile(level)
    cmds = stacks.commands_for(stacks_keys)
    return {
        "$schema": SCHEMA,
        "permissions": {
            "defaultMode": prof["default_mode"],
            "allow": cmds["allow"] + ["Bash(git status)", "Bash(git diff *)"],
            "ask": cmds["ask"] + ["Bash(git commit *)"],
            "deny": _deny_reads(extra_deny_paths)
                    + [f"Bash({c})" for c in rules.BASE_DENY_COMMANDS],
        },
        "sandbox": {
            "enabled": True,
            "autoAllowBashIfSandboxed": False,
            "allowUnsandboxedCommands": False,
            "filesystem": {"denyRead": list(rules.CREDENTIAL_DIRS)},
            "network": {"allowedDomains": list(allowed_domains)},
        },
    }


def build_managed_settings(level, stacks_keys, allowed_domains, extra_deny_paths,
                           denied_domains, claude_min_version=None):
    prof = rules.level_profile(level)
    cmds = stacks.commands_for(stacks_keys)
    settings = {
        "$schema": SCHEMA,
        "disableArtifact": True,
        "disableRemoteControl": True,
        "disableClaudeAiConnectors": True,
        "autoMemoryEnabled": False,
        "cleanupPeriodDays": 7,
        "permissions": {
            "defaultMode": prof["default_mode"],
            "disableBypassPermissionsMode": "disable",
            "disableAutoMode": "disable",
            "allow": ["Bash(git status)", "Bash(git diff *)"],
            "ask": cmds["ask"],
            "deny": _deny_reads(extra_deny_paths) + ["WebSearch"]
                    + [f"Bash({c})" for c in rules.BASE_DENY_COMMANDS],
        },
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": prof["sandbox_fail_if_unavailable"],
            "autoAllowBashIfSandboxed": False,
            "allowUnsandboxedCommands": False,
            "filesystem": {
                "denyRead": list(rules.CREDENTIAL_DIRS),
                "allowManagedReadPathsOnly": True,
            },
            "network": {
                "allowedDomains": list(allowed_domains),
                "deniedDomains": list(denied_domains),
                "allowManagedDomainsOnly": True,
            },
        },
        "allowedMcpServers": [],
        "allowManagedMcpServersOnly": True,
        "allowManagedPermissionRulesOnly": True,
        "allowManagedHooksOnly": True,
        "disableSkillShellExecution": True,
    }
    if claude_min_version:
        settings["requiredMinimumVersion"] = claude_min_version
    return settings
