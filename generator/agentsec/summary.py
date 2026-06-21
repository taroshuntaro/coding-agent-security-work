"""生成前に表示する入力サマリの整形（純関数）。"""

_REDLINE_LABELS = [
    ("use_full_access", "フルアクセス常用"),
    ("share_docker_socket", "Docker ソケット共有"),
    ("network_host", "ホストネットワーク"),
    ("direct_push", "直接 push/deploy"),
]


def _join(items):
    return ", ".join(items) if items else "なし"


def _yn(value):
    return "はい" if value else "いいえ"


def format_summary(profile):
    redlines = "、".join(
        f"{label}={_yn(profile.get(key, False))}"
        for key, label in _REDLINE_LABELS)
    return "\n".join([
        "=== 生成内容の確認 ===",
        f"製品: {_join(profile['products'])}",
        f"レベル: {profile['level']} / プラン: {profile['plan']}",
        f"スタック: {_join(profile['stacks'])}",
        f"許可ドメイン: {_join(profile['allowed_domains'])}",
        f"追加 deny パス: {_join(profile['extra_deny_paths'])}",
        f"コンテナ定義: {'生成する' if profile['use_container'] else '生成しない'}",
        f"レッドライン: {redlines}",
    ])
