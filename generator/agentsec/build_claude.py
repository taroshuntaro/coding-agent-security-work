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
            "allow": cmds["allow"] + ["Bash(git status)", "Bash(git diff *)",
                                      "Bash(git log *)"],
            "ask": cmds["ask"] + ["Bash(git commit *)", "WebSearch"],
            "deny": _deny_reads(extra_deny_paths)
                    + [f"Bash({c})" for c in rules.BASE_DENY_COMMANDS],
        },
        "sandbox": {
            "enabled": True,
            "autoAllowBashIfSandboxed": False,
            "allowUnsandboxedCommands": False,
            "filesystem": {"denyRead": list(rules.CREDENTIAL_DIRS)},
            # strictAllowlist はここに置かない: user / managed / --settings でのみ有効で、
            # リポジトリの .claude/settings.json に置いても無視される（docs/11 11.4）。
            # 個人系は ~/.claude/settings.json、チーム系は managed-settings.json に置く。
            "network": {"allowedDomains": list(allowed_domains)},
        },
    }


def build_managed_settings(level, stacks_keys, allowed_domains, extra_deny_paths,
                           denied_domains, claude_min_version=None):
    prof = rules.level_profile(level)
    cmds = stacks.commands_for(stacks_keys)
    settings = {
        "$schema": SCHEMA,
        # Artifact ロックは新旧2キーを併記する（docs/11 11.5）。
        # enableArtifact は v2.1.196 以降でのみ認識されるため、それ未満の
        # クライアントではロックが外れる。公式が同等と認める旧キー
        # disableArtifact: true を残し、どのバージョンでも無効化されるようにする。
        "enableArtifact": False,
        "disableArtifact": True,
        "disableRemoteControl": True,
        "disableClaudeAiConnectors": True,
        # セッション間メッセージ（docs/11 11.11）: 機密案件では受信を拒否し、
        # 他マシンの自セッションへの送信は bypass 中でも承認を求める。
        "crossSessionInbound": "refuse",
        "isolatePeerMachines": True,
        "autoMemoryEnabled": False,
        "cleanupPeriodDays": 7,
        "permissions": {
            "defaultMode": prof["default_mode"],
            "disableBypassPermissionsMode": "disable",
            "disableAutoMode": "disable",
            "allow": ["Bash(git status)", "Bash(git diff *)", "Bash(git log *)"],
            "ask": cmds["ask"] + ["Bash(git commit *)"],
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
                "strictAllowlist": True,
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
