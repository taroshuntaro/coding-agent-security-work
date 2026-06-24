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
- 許可リスト（`allowedMcpServers`）に加え、明示拒否（`deniedMcpServers`）を併用する（denylist 優先）

## 13.3 プラン別の強制

- **チーム・ビジネス系プラン**: 管理者がMCP allowlistを強制できる（Codex MCP identity allowlist、Claude Code `allowManagedMcpServersOnly` / `allowedMcpServers` / `allowManagedHooksOnly`。[10.5](10-codex.md)・[11.5](11-claude-code.md)）。
- **個人系プラン**: 管理者強制は使えない。利用者が許可リストを自己管理し、任意追加しない運用＋[15 受入テスト](15-acceptance-tests.md)で代替する。第三者強制が要件となる案件には不適（[00 R6](00-red-lines.md)）。

[← 目次へ戻る](README.md) ｜ [次：14 Git・CI/CD・本番操作 →](14-git-cicd.md)
