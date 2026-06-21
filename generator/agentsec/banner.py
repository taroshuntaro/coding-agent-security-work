"""コメント可ファイル（TOML/Dockerfile/compose）へ前置する自己説明バナー。"""


def banner(level, products):
    prod = ", ".join(products)
    lines = [
        "# === 自動生成: coding-agent-security 設定ジェネレータ ===",
        f"# レベル: {level} / 製品: {prod}",
        "# 値の正典は docs/（00-red-lines.md 等）。変更時は docs と整合させること。",
        "# 再生成すると本ファイルは上書きされます。手元の変更は別管理を。",
    ]
    return "\n".join(lines) + "\n"
