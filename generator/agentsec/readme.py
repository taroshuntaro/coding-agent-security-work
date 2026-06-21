"""生成された成果物に応じた README 用テキストの整形（純関数）。

JSON はコメントを持てないため、各成果物の役割と適用手順はここで補完する。
"""

# (相対パス, 役割説明) を生成順に定義。生成されたものだけを出力する。
_ROLES = [
    ("claude-code/.claude/settings.json",
     "Claude Code のプロジェクト設定（補助設定）。リポジトリへ配置。"),
    ("claude-code/managed-settings.json",
     "Claude Code の組織強制設定（team かつ L3+）。リポジトリ外の管理パスへ配置。"),
    ("codex/.codex/config.toml",
     "Codex の開発者設定。先頭コメントの extends 前提を確認のうえ配置。"),
    ("codex/requirements.toml",
     "Codex の組織管理要件（team）。管理側へ配置。"),
    ("Dockerfile", "非 root・最小権限の実行コンテナ定義。"),
    ("docker-compose.yml", "read_only・cap_drop 等を含む起動定義。"),
    (".devcontainer/devcontainer.json", "VS Code devcontainer 定義。"),
    (".dockerignore", "コンテキスト除外設定。"),
    ("acceptance/checklist.md", "受入テストのチェックリスト（docs/15 準拠）。"),
    ("acceptance/selfcheck.py", "レッドラインの静的検査スクリプト（standalone）。"),
    ("POLICY-SHEET.md", "案件別ポリシー記入シート（逸脱を明記）。"),
    ("generation-profile.json", "再現用プロファイル + 各ファイルの SHA-256・逸脱レジスタ。"),
]


def artifact_guide(file_keys):
    lines = [f"- `{rel}` — {role}" for rel, role in _ROLES if rel in file_keys]
    return "\n".join(lines)


def apply_steps(file_keys):
    steps = []
    if "claude-code/.claude/settings.json" in file_keys:
        steps.append("- Claude Code: `claude-code/.claude/settings.json` をリポジトリへ配置")
    if "claude-code/managed-settings.json" in file_keys:
        steps.append("- Claude Code 管理設定: `claude-code/managed-settings.json` を"
                     "リポジトリ外の管理パスへ配置")
    if "codex/.codex/config.toml" in file_keys:
        steps.append("- Codex: `codex/.codex/config.toml` を配置")
    if "codex/requirements.toml" in file_keys:
        steps.append("- Codex 管理要件: `codex/requirements.toml` を管理側へ配置")
    if "Dockerfile" in file_keys:
        steps.append("- コンテナ: `Dockerfile` / `docker-compose.yml` / `.devcontainer/` を利用")
    return "\n".join(steps)


def placement_guide(file_keys):
    """生成成果物に応じて配置3層・優先順位・R6 注記を返す（純関数）。"""
    has_managed = ("claude-code/managed-settings.json" in file_keys
                   or "codex/requirements.toml" in file_keys)
    has_local = ("claude-code/.claude/settings.json" in file_keys
                 or "codex/.codex/config.toml" in file_keys)
    lines = ["設定は強制力で層が分かれます。**守らせたい統制は最上位（管理層）へ"
             "リポジトリ外から配置**してください（docs/00 R6）。", "",
             "| 層 | 強制力 | 配置先 |", "|---|---|---|"]
    if has_managed:
        lines.append("| 管理 | 利用者/エージェントが解除不能 | "
                     "**リポジトリ外**（OS 管理パス・MDM・コンテナイメージ） |")
    if has_local:
        lines.append("| プロジェクト/ユーザー | 書き換え可能＝強制ではない | "
                     "リポジトリ内 `.claude/` ／ コンテナ home `~/.codex/` |")
    lines += ["",
              "- 優先順位: **管理 > プロジェクト > ユーザー**。ガードレールは管理層に置き、"
              "`*ManagedOnly` 系で下位層からの再許可を抑止する。",
              "- **R6**: `.claude/`・`.codex/`・`CLAUDE.md`・`AGENTS.md` 等はリポジトリを"
              "書ける主体（エージェント自身を含む）が変更できるため、**強制ポリシーとみなさない**。",
              "- スタック別 allow/ask（`npm test` 等）はプロジェクト層の補助。"
              "レッドライン・egress 許可・資格情報 denyRead は管理層で固定する。"]
    if has_local:
        lines.append(
            "- モノレポ／複数プロジェクトを1コンテナにマウントする場合も、助言設定"
            "（`.claude/`・`.codex/`）は**ワークスペース/コンテナ共通の場所（例：コンテナ home の "
            "`~/.claude/`・`~/.codex/`）に1つ**置けば全サブプロジェクト・全マウントに効く"
            "（権限はメイン/サブ一律）。")
    return "\n".join(lines)
