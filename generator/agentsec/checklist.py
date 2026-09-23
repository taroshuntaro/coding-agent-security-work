"""受入テスト チェックリストの製品別追加行（純関数）。docs/15-acceptance-tests.md 準拠。

設定を「書いた」だけでは効かないケース（有効スコープ違い・既定値の変化）を
実環境で確かめるための行を、生成対象の製品に応じて返す。
"""

# (製品キー, 行) を docs/15 の並びで定義する。
_ROWS = [
    ("claude",
     "| `strictAllowlist` を user / managed 設定に置いたとき、許可リスト外ホストへの"
     "サンドボックス内通信が確認なしで拒否される（プロジェクト設定だけに置くと"
     "確認プロンプトに落ちることも確認） | 拒否 | |"),
    ("claude",
     "| `permissions.defaultMode` の指定どおりの開始モードになる"
     "（ターミナルと VS Code 拡張の両方。Pro/Max/Team の組み込み既定は auto mode） | 指定モードで開始 | |"),
    ("claude",
     "| `blockReadsOutsideWorkingDirectories` 採用時、作業ディレクトリ外の "
     "Read/Grep/Glob と `cat ~/.ssh/...` が拒否または確認される | 拒否または確認 | |"),
    ("claude",
     "| `crossSessionInbound: \"refuse\"` 採用時、他セッションからの `SendMessage` が届かない"
     " | 拒否 | |"),
    ("codex",
     "| auto-review（Guardian）採用時、`.env` 読み取り・`git push`・ワークスペース外書き込みの"
     " escalation が自動承認されない | 拒否または人間の承認 | |"),
]


def extra_rows(products):
    """products に含まれる製品の追加行を、改行区切りの markdown 表行として返す。"""
    return "\n".join(row for product, row in _ROWS if product in products)
