# 13 MCP・Plugins・Hooksの統制

[← 目次へ戻る](README.md)

## 13.1 基本方針

MCP、プラグイン、Hooksは、エージェントの能力を拡張すると同時に、新しい権限・通信・コード実行経路を追加する。

各連携について、少なくとも次を記録する。

- 所有者
- 提供元
- バージョン
- 実行方式
- 接続先
- 読み取り権限
- 書き込み権限
- 使用する認証情報
- ログ・保存データ
- 更新方法
- インシデント時の無効化方法

## 13.2 推奨

- deny by default
- 管理者許可リスト
- 案件単位の設定
- 読み取り専用を優先
- OAuth scope・API権限を最小化
- 本番環境の書き込み権限を付与しない
- 任意のローカルコマンドを実行するMCPを厳格審査
- リモートMCPのドメインをネットワーク許可リストへ反映
- 設定ファイルを信頼する前にレビュー
- 更新時に再審査
- 許可リストに加え、明示拒否リストを併用する（拒否を優先）
- CLI引数など、リポジトリ外・未審査の経路からの連携注入（sideload）を起動時に拒否する
- 一律停止が必要な環境では、Hooksを全面無効化できる設定を用意しておく
- 任意URLへ送信するHooks（HTTP Hooks等）は外部送信経路として扱い、送信先URLと送信に使える環境変数を許可リストで限定する
- プラグイン・拡張の供給元（マーケットプレイス等）を許可リストで固定し、インストール時にスクリプトを実行する供給経路を禁止する
- user / project 由来の拡張（スキル・サブエージェント・Hooks・MCP）を一括遮断し、組織配布分だけに限定できる製品では、上位レベルで採用を検討する
- 組織配布した連携にも許可・拒否リストが効くかを確認する（許可リストが利用者追加分だけを対象とする製品がある）

### 製品別の実装例

上記の統制目標を、Claude Code・Codexでは次の設定で実装できる。他製品では同じ目的の機能に読み替える。設定キーと対応バージョンは変動するため、[付録C](appendix-c-volatile-values.md)と[10](10-codex.md)・[11](11-claude-code.md)章で確認する。

- 許可リスト（`allowedMcpServers`）に加え、明示拒否（`deniedMcpServers`）を併用する（denylist 優先）
- `.mcp.json` 由来の特定サーバーは `disabledMcpjsonServers`（Claude Code）で名指し拒否できる（許可／拒否リストの補完。[付録C](appendix-c-volatile-values.md)）
- CLIからの sideload（`--mcp-config`・`--plugin-dir`・`--plugin-url`・`--agents`）は `disableSideloadFlags`（Claude Code）で起動時に拒否し、リポジトリ外・未審査の連携注入を防ぐ（[付録C](appendix-c-volatile-values.md)）
- Hooksを一律に停止する必要がある環境では `disableAllHooks`（Claude Code。全Hooks＋カスタムstatuslineを無効化）を使う（[付録C](appendix-c-volatile-values.md)）
- **HTTP Hooks**（Claude Code。`type: "http"` で任意 URL へ POST）は外部送信経路になる。`allowedHttpHookUrls`（空配列で全面遮断。全スコープでマージされ、managed 由来の Hook にも適用）と `httpHookAllowedEnvVars`（ヘッダへ展開できる環境変数の限定）で絞る。managed 側の値が読めないときは v2.1.267 以降「何も許可しない」に倒れる
- **プラグイン供給元**（Claude Code）: `strictKnownMarketplaces`（許可マーケットプレイスのみ。空配列で全面禁止）・`blockedMarketplaces`（`owner/*` ワイルドカード可）・`disableCommandPluginSources`（マーケットプレイス宣言のローカルコマンド実行によるインストールを禁止。`allowManagedHooksOnly` 有効時は既定で禁止）。npm ソースのプラグインは v2.1.275 以降 `--ignore-scripts` で取得され、インストールスクリプトは実行されない
- **user / project 由来の拡張を一括遮断**（Claude Code）: `strictPluginOnlyCustomization`（`skills`・`agents`・`hooks`・`mcp`）。プラグインと管理設定由来だけを残し、`strictKnownMarketplaces` と組み合わせて供給網全体を固定する（[11.9](11-claude-code.md)）。プロジェクトのサブエージェント定義に書かれた Hooks は、フォルダの信頼ダイアログ承認後にのみ実行される（v2.1.218 以降）
- v2.1.259 以降、Claude Code の `allowedMcpServers` は**利用者が追加したサーバーだけ**を対象とする。`managed-mcp.json` や `managedMcpServers` で組織配布したサーバーを止めるには `deniedMcpServers` を使う（denylist はどの配布経路のサーバーにも効く）
- Codex の Hooks は非同期実行・MCP ツール呼び出しに対応した（0.148.0）。`allow_managed_hooks_only = true` は `requirements.toml` でのみ有効で、`config.toml` に置いても managed-hooks-only にならない（openai/codex `docs/config.md`）

> [!NOTE]
> Hook の戻り値は権限 deny を無効化できない前提で設計する。`PreToolUse` Hook の `allow` がバックグラウンドタスクのツール制限を迂回できた不具合は v2.1.222 で修正され、critical path（`/`・ホーム・作業ディレクトリ等）への `rm` は allow ルールでも `PreToolUse` の `allow` でも承認されない（2026-09-21 確認）。とはいえ deny は権限ルール側・サンドボックス側で担保し、Hook は監査・補助に使う。

## 13.3 プラン別の強制

- **チーム・ビジネス系プラン**: 管理者がMCP allowlistを強制できる（Codex MCP identity allowlist、Claude Code `allowManagedMcpServersOnly` / `allowedMcpServers` / `allowManagedHooksOnly`。[10.5](10-codex.md)・[11.5](11-claude-code.md)）。
- **個人系プラン**: 管理者強制は使えない。利用者が許可リストを自己管理し、任意追加しない運用＋[15 受入テスト](15-acceptance-tests.md)で代替する。第三者強制が要件となる案件には不適（[00 R6](00-red-lines.md)）。

## 13.4 MCP特有の脅威

MCPサーバーは、権限を持つ実行主体であると同時に、**エージェントへテキストを供給する入力源**でもある。MCP仕様も、ツールの挙動の説明（annotations等）は信頼できるサーバー由来でない限り非信頼として扱うよう求めている。13.2の権限統制に加え、次を前提に審査する。以下の呼称（tool poisoning・rug pull）はMCP公式の用語ではなく、セキュリティ業界で広く使われている呼び名である。

- **ツール定義への指示埋め込み（tool poisoning）**: ツールの名前・説明文・引数スキーマはモデルへそのまま渡る。説明文に隠れた指示（他のツールの使い方の変更、ファイルの読み取りと送信など）を埋め込める。導入時にツール定義の全文を確認する。
- **承認後の定義変更（rug pull）**: 審査時と異なるツール定義を、後から配信できる。バージョンを固定し、ツール定義の変化を検知したら再審査する。リモートMCPは提供元がいつでも変更できる前提で扱う。
- **実行結果経由の注入**: 外部データ（Issue、メール、Webページ、チケット本文等）を返すツールの結果は非信頼入力である。書き込み・送信系のツールと同じセッションで使う場合は[3.2](03-risks.md)の3要素に当たる。
- **ツール名の衝突・なりすまし**: 複数サーバーが似た名前のツールを提供すると、意図しないサーバーのツールが呼ばれ得る。許可するサーバーを絞り、名前空間を確認する。
- **認可とトークン**: リモートMCPの認可はOAuthで行う。トークンは対象サーバー専用（audienceを限定）にし、scopeを最小にする。MCPサーバーが受け取ったトークンをそのまま別のAPIへ転送する実装（token passthrough）や、MCPサーバーが利用者の代わりに第三者APIへ過剰な権限でアクセスする構成（confused deputy）を避ける。いずれもMCP公式のSecurity Best Practicesで扱われている（[20](20-references.md)）。
- **ローカルMCPの実行権限**: stdio型のローカルMCPは、エージェントと同じ権限でホスト上のコマンドとして動く。起動コマンド・引数を固定し、サンドボックスやコンテナの内側で動かす。

[← 目次へ戻る](README.md) ｜ [次：14 Git・CI/CD・本番操作 →](14-git-cicd.md)
