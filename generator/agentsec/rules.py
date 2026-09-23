"""レベル×プラン×製品ごとの設定ルールをデータとして定義する。

docs/00-red-lines.md, docs/10-codex.md, docs/11-claude-code.md の具体値に対応。
"""

LEVELS = ("L1", "L2", "L3", "L4")
PLANS = ("personal", "team")
PRODUCTS = ("claude", "codex")

BASE_DENY_COMMANDS = [
    "curl *", "wget *", "ssh *", "scp *", "sudo *",
    "kubectl *", "helm *", "terraform apply *", "terraform destroy *",
    "git push *",
]

SENSITIVE_READ_PATHS = [
    "./.env", "./.env.*", "./secrets/**", "./config/credentials.json",
]

# ホーム配下の資格情報（docs/08 8.7）。トークン専用の保存場所だけを既定で読み取り拒否する。
# ~/.npmrc・~/.gradle/gradle.properties・~/.m2/settings.xml はビルド時に読まれ、
# 拒否するとインストール・ビルドが壊れるため含めない（docs/11 11.4）。
CREDENTIAL_PATHS = [
    "~/.ssh", "~/.aws", "~/.kube", "~/.config/gcloud", "~/.azure",
    "~/.config/gh", "~/.git-credentials", "~/.netrc",
    "~/.docker/config.json", "~/.pypirc",
]

DEFAULT_ALLOWED_DOMAINS = ["github.com", "objects.githubusercontent.com"]

_LEVEL_PROFILES = {
    "L1": {"default_mode": "plan", "managed_required": False,
           "sandbox_fail_if_unavailable": False, "web_search": "cached"},
    "L2": {"default_mode": "default", "managed_required": False,
           "sandbox_fail_if_unavailable": False, "web_search": "cached"},
    "L3": {"default_mode": "default", "managed_required": True,
           "sandbox_fail_if_unavailable": True, "web_search": "cached"},
    "L4": {"default_mode": "default", "managed_required": True,
           "sandbox_fail_if_unavailable": True, "web_search": "disabled"},
}


def level_profile(level):
    if level not in _LEVEL_PROFILES:
        raise ValueError(f"unknown level: {level}")
    return dict(_LEVEL_PROFILES[level])
