"""対話の質問定義（純データ）と回答解釈・プロンプト整形（純ロジック）。

対話 I/O（input/print）は generate.py に置く。ここは引数で値を受け取り
テスト可能な純関数のみを提供する。
"""

from agentsec import rules, stacks

_STACK_LIST = ", ".join(sorted(stacks.KNOWN))

QUESTIONS = [
    {"key": "include_claude", "type": "yesno", "default": "y",
     "prompt": "Claude Code を対象に含めますか",
     "help_line": "Claude Code 用の設定を生成します。",
     "detail": "settings.json（team かつ L3+ では managed-settings.json も）を出力します。"},
    {"key": "include_codex", "type": "yesno", "default": "y",
     "prompt": "Codex を対象に含めますか",
     "help_line": "Codex 用の設定を生成します。",
     "detail": "config.toml（team では requirements.toml も）を出力します。"},
    {"key": "level", "type": "choice", "choices": list(rules.LEVELS), "default": "L2",
     "prompt": "利用レベル",
     "help_line": "与える権限の段階。番号が大きいほど制限が強い。",
     "detail": ("L1=計画/読み取り中心の最小権限。L2=ワークスペース編集ありの標準。"
                "L3=組織の強制設定を適用。L4=Web 検索も遮断する最も厳格な構成。迷ったら L2。")},
    {"key": "plan", "type": "choice", "choices": list(rules.PLANS), "default": "team",
     "prompt": "契約プラン",
     "help_line": "個人契約(personal)か、チーム/ビジネス契約(team)か。",
     "detail": ("team かつ L3+ のときのみ組織強制設定"
                "（managed-settings.json / requirements.toml）を生成します。")},
    {"key": "stacks", "type": "csv", "default": [],
     "prompt": "ビルド/言語スタック（カンマ区切り、無ければ空 Enter）",
     "help_line": f"対象プロジェクトで使うものを選びます。対応: {_STACK_LIST}。",
     "detail": ("ここで挙げたスタックの test/build 等を許可コマンドに追加します。"
                f"対応 = {_STACK_LIST}。未対応のものは空のままにし、生成後に手動で追加してください。")},
    {"key": "allowed_domains", "type": "csv",
     "default": list(rules.DEFAULT_ALLOWED_DOMAINS),
     "prompt": "許可するネットワークドメイン（カンマ区切り）",
     "help_line": "エージェントが接続してよいドメインだけを列挙します。",
     "detail": ("空 Enter で既定 "
                f"({', '.join(rules.DEFAULT_ALLOWED_DOMAINS)}) を採用します。"
                "ここに無いドメインへの接続は遮断されます。")},
    {"key": "extra_deny_paths", "type": "csv", "default": [],
     "prompt": "追加で読み取り禁止にするパス（カンマ区切り、無ければ空 Enter）",
     "help_line": "既定の .env / secrets に加えて読み取りを禁止したいパス。",
     "detail": "例: **/keys/**, ./private/**。空 Enter なら既定の機密パスのみを禁止します。"},
    {"key": "use_container", "type": "yesno", "default": "y",
     "prompt": "コンテナ定義（Dockerfile 等）を出力しますか",
     "help_line": "非 root・最小権限のコンテナ定義一式を生成します。",
     "detail": "Dockerfile / docker-compose.yml / .devcontainer / .dockerignore を出力します。"},
    {"key": "use_full_access", "type": "yesno", "default": "n",
     "prompt": "権限バイパス/フルアクセスを常用しますか",
     "help_line": "（レッドライン）原則いいえ。安全側の既定は n。",
     "detail": ("はいにすると承認なしで任意コマンドを実行でき、隔離の意味が失われます。"
                "docs/00-red-lines.md の MUST 違反。既定の n を推奨。")},
    {"key": "share_docker_socket", "type": "yesno", "default": "n",
     "prompt": "コンテナへ Docker ソケットを共有しますか",
     "help_line": "（レッドライン）原則いいえ。安全側の既定は n。",
     "detail": ("ホストの Docker デーモンを操作できるようになり、実質ホスト root 相当の"
                "奪取が可能になります。docs/00-red-lines.md の MUST 違反。既定の n を推奨。")},
    {"key": "network_host", "type": "yesno", "default": "n",
     "prompt": "ホストネットワークを使用しますか",
     "help_line": "（レッドライン）原則いいえ。安全側の既定は n。",
     "detail": ("コンテナのネットワーク隔離が外れ、ホストの localhost や内部サービスへ"
                "到達可能になります。docs/00-red-lines.md の MUST 違反。既定の n を推奨。")},
    {"key": "direct_push", "type": "yesno", "default": "n",
     "prompt": "エージェントに直接 push/deploy を行わせますか",
     "help_line": "（レッドライン）原則いいえ。安全側の既定は n。",
     "detail": ("リモートや本番への変更はエージェント外（人/パイプライン）で行うべきです。"
                "docs/00-red-lines.md の MUST 違反。既定の n を推奨。")},
]


def _default_display(q):
    if q["type"] == "csv":
        d = q["default"]
        return ", ".join(d) if d else "なし"
    return q["default"]


def render_prompt(q):
    return (f"{q['prompt']} （既定: {_default_display(q)} — {q['help_line']}"
            f" ／ ? で詳細）: ")


def resolve_answer(q, raw):
    raw = raw.strip()
    if raw == "?":
        return ("help", None)

    if q["type"] == "yesno":
        if raw == "":
            raw = q["default"]
        if raw not in ("y", "n"):
            return ("error", "y または n を入力してください")
        return ("ok", raw == "y")

    if q["type"] == "choice":
        if raw == "":
            raw = q["default"]
        if raw not in q["choices"]:
            return ("error", f"次から選んでください: {', '.join(q['choices'])}")
        return ("ok", raw)

    # csv
    if raw == "":
        return ("ok", list(q["default"]))
    return ("ok", [s.strip() for s in raw.split(",") if s.strip()])
