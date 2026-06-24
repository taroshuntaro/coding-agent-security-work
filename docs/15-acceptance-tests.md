# 15 ポリシー受入テスト

[← 目次へ戻る](README.md)

設定ファイルを配布しただけで完了とせず、対象OS・製品バージョン・実行形態ごとにテストする（[00 R5](00-red-lines.md)）。テスト用のダミー値と隔離環境を使用し、本物のシークレットや本番サービスを使わない。

> [!IMPORTANT]
> **「設定したのに効かない」は理論ではなく実際に起きている。** たとえばClaude Codeの `disableBypassPermissionsMode` は、managed-settings.jsonに記述しても特定バージョンで無効だった実例がある（[Issue #44642](https://github.com/anthropics/claude-code/issues/44642)）。`autoAllowBashIfSandboxed` にもシェル展開やサンドボックス無効化コマンドによるバイパス報告がある（[#29016](https://github.com/anthropics/claude-code/issues/29016)、[#43713](https://github.com/anthropics/claude-code/issues/43713)）。だからこそ、設定の**存在**ではなく**実拒否**を確認する。

## 15.1 テストマトリクス

| テスト | 期待結果 |
|---|---|
| ワークスペース内の通常ファイルを読む | 許可 |
| `.env`、`secrets/`、ホスト資格情報を読む | 拒否 |
| ワークスペース内の通常ファイルを変更 | 対象レベルに応じて許可または承認 |
| ワークスペース外へ書き込む | 拒否または明示的承認 |
| `curl`等で未許可ドメインへ通信 | 拒否 |
| 許可したパッケージレジストリへ通信 | 必要な場合のみ許可 |
| `git push`、`terraform apply`、`kubectl`変更操作 | 拒否または独立した承認フロー |
| 未承認MCP・Hooks・Pluginsを追加 | 無効化または拒否 |
| bypass / full access を起動・選択 | （L2以上）拒否または管理的に不可 |
| sandbox依存が欠けた状態で起動 | 機密レベルでは起動失敗 |
| managed policyを取得できない状態 | 想定したfail-open / fail-closed挙動 |
| コンテナ内からホストのホーム、Docker socketへアクセス | 拒否 |
| セッション終了・環境破棄後 | シークレット、履歴、不要キャッシュが残らない |
| 製品アップデート後 | 同じテスト結果が維持される |
| `requiredMinimumVersion` を設定したとき、それ未満のクライアントで起動が拒否されること（チーム系 L3+） | 拒否 |
| プロジェクト設定で `denyRead:["~/"]＋allowRead:["."]` を用いた場合に、`~/.ssh` 等が読めず、プロジェクト内ファイルは読めること（堅牢パターン採用時） | `~/.ssh` は拒否・プロジェクト内は許可 |

## 15.2 記録

検証結果は、製品バージョン、OS、設定ファイルのハッシュ、実施日、実施者とともに記録する。プラン（個人系／チーム・ビジネス系）と、その案件のレベルも併記する。

[← 目次へ戻る](README.md) ｜ [次：16 導入前チェックリスト →](16-pre-adoption-checklist.md)
