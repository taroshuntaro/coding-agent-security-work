# 15 ポリシー受入テスト

[← 目次へ戻る](README.md)

設定ファイルを配布しただけで完了とせず、対象OS・製品バージョン・実行形態ごとにテストする（[00 R5](00-red-lines.md)）。テスト用のダミー値と隔離環境を使用し、本物のシークレットや本番サービスを使わない。

> [!IMPORTANT]
> **「設定したのに効かない」は理論ではなく実際に起きている。** たとえばClaude Codeの `disableBypassPermissionsMode` は、managed-settings.jsonに記述しても特定バージョンで無効だった実例があり、同Issueは修正されないままcloseされている（[Issue #44642](https://github.com/anthropics/claude-code/issues/44642)、closed as not planned・2026-09-21 再確認）。`autoAllowBashIfSandboxed` にもサンドボックス無効化コマンドの自動承認によるバイパス報告がある（[#29016](https://github.com/anthropics/claude-code/issues/29016)、closed・修正バージョン未特定。[#43713](https://github.com/anthropics/claude-code/issues/43713) は過剰プロンプトの別件で closed）。さらに `strictAllowlist` のように**置く場所（user / project / managed）によって無視される**キーもある（[11.4](11-claude-code.md)）。だからこそ、設定の**存在**ではなく**実拒否**を確認する。

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

### 製品別の追加観点（Claude Code・Codex）

上表の共通観点に加え、2製品では次の「書いても効かないことがある」設定を確認する。他製品では、同様に**置き場所・前提条件・既定値の変化で効かなくなる設定**を洗い出して行を追加する。

| テスト | 期待結果 |
|---|---|
| `requiredMinimumVersion` を設定したとき、それ未満のクライアントで起動が拒否されること（チーム系 L3+） | 拒否 |
| プロジェクト設定で `denyRead:["~/"]＋allowRead:["."]` を用いた場合に、`~/.ssh` 等が読めず、プロジェクト内ファイルは読めること（堅牢パターン採用時） | `~/.ssh` は拒否・プロジェクト内は許可 |
| `strictAllowlist` を user / managed 設定に置いたとき、許可リスト外ホストへのサンドボックス内通信が**確認なしで拒否**されること（プロジェクト設定だけに置いた状態では確認プロンプトに落ちることも併せて確認） | 拒否 |
| Pro/Max/Team プランで、`permissions.defaultMode` の指定どおりの開始モードになること（ターミナル・VS Code 拡張の両方。管理設定で `disableAutoMode` を置いた場合は auto mode を選択できないこと） | 指定モードで開始・auto は選択不可 |
| `permissions.blockReadsOutsideWorkingDirectories` 採用時に、作業ディレクトリ外（ホーム配下）の Read/Grep/Glob と `cat ~/.ssh/...` が拒否または確認されること | 拒否または確認 |
| `crossSessionInbound: "refuse"` のとき、他セッションからの `SendMessage` が届かないこと（採用時） | 拒否 |
| Codex でドメイン許可リストを設定したとき、許可リスト外ホストへのサンドボックス内通信が拒否されること（`features.network_proxy` または管理側 `[experimental_network]` が無いと直接通信になるため、設定の有無と実拒否の両方を確認。[10.4](10-codex.md)） | 拒否 |
| Codex auto-review（Guardian）採用時、`.env` 読み取り・`git push`・ワークスペース外書き込みの escalation が自動承認されないこと | 拒否または人間の承認 |

> [!NOTE]
> 生成ツール（`generator/`）は、上記「製品別の追加観点」表の行のうち一部を `acceptance/checklist.md` へ出力する（Claude Code 向け4行・Codex 向け2行）。本表を更新したときは生成ツール側（`agentsec/checklist.py`）も合わせて更新する。

## 15.2 記録

検証結果は、製品バージョン、OS、設定ファイルのハッシュ、実施日、実施者とともに記録する。プラン（個人系／チーム・ビジネス系）と、その案件のレベルも併記する。

[← 目次へ戻る](README.md) ｜ [次：16 導入前チェックリスト →](16-pre-adoption-checklist.md)
