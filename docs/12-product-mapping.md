# 12 CodexとClaude Codeの対応関係

[← 目次へ戻る](README.md)

| 設計上の目的 | Codex | Claude Code |
|---|---|---|
| 読み取り専用 | `:read-only`、旧`read-only` sandbox | `plan`、`default`＋deny |
| ワークスペース書込 | `:workspace`、カスタムpermission profile | `acceptEdits`またはallow rules |
| コマンド前確認 | `approval_policy` | permission mode、ask rules |
| OSレベル制限 | sandbox / permission profile | sandbox filesystem/network |
| 機密ファイルdeny | permission profile filesystem deny | `permissions.deny`＋sandbox denyRead |
| コマンドネットワーク | permission profile network | sandbox network |
| 組み込みWeb機能 | `web_search`（`disabled` / `cached` / `live`） | `WebSearch`、`WebFetch`のpermission rule。Bash通信は別制御 |
| 管理強制 | `requirements.toml`、managed config | managed settings |
| 全権限 | `:danger-full-access` | `bypassPermissions` |
| 外部ツール | MCP設定・管理制限 | MCP・Hooks・Pluginsの管理制限 |
| 外側の隔離 | コンテナ・VMを別途利用 | 開発コンテナ・VMを別途利用 |

製品間で名称を揃えることより、次の実効権限を揃えることが重要である（[19 最終的な判断基準](19-final-criteria.md)）。

```text
- 何を読めるか
- 何を書けるか
- 何を実行できるか
- どこへ通信できるか
- どの認証情報を使えるか
- どの外部システムを操作できるか
- 誰が設定を変更できるか
- 何が監査記録に残るか
```

> [!NOTE]
> この対応表は製品非依存層と製品固有層の橋渡しである。Codex/Claude Code以外の製品でも、左列の「設計上の目的」を各製品の機能へ対応づけて使う（[README スコープ](README.md)）。

[← 目次へ戻る](README.md) ｜ [次：13 MCP・Plugins・Hooksの統制 →](13-mcp-plugins-hooks.md)
