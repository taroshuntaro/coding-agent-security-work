# 付録C 揮発値一覧（バージョン・既定値・設定キー）

[← 目次へ戻る](README.md)

本文中の「変動しやすい具体値」をここに集約する。製品更新時は**本表だけを洗い、確認日を更新**すればよい（[17.2](17-periodic-review.md)）。本文の設定例コードブロックは各製品章に残してある。

- **基準確認日**: 2026-09-21（Claude Code。CHANGELOG は v2.1.278 まで確認）／ 2026-09-23（Codex。公式ドキュメントとリリースノートは 0.156.0 まで確認）
- **検証状態**の凡例: ✅ 一次資料（公式ドキュメント／GitHub）で確認済み ／ ⚠️ 本ガイド作成時点で未再検証（旧版記述を引き継ぎ。導入時に要確認）

## C.1 Codex

> [!NOTE]
> `developers.openai.com/codex` 配下のドキュメントは `learn.chatgpt.com/docs` 配下へ恒久移転している（308リダイレクトを 2026-08-04 に確認）。旧URLもリダイレクトで到達できる。本表の出典は移転先を確認できたものから新URLへ更新している。
>
> **2026-09-23 の再検証について**: 2026-09-21 には作業環境から公式ドキュメントへ到達できず、設定リファレンス由来の値を 2026-08-04 確認のまま据え置いていた。2026-09-23 に公式ドキュメント（config-reference・managed-configuration・permissions・agent-approvals-security・auto-review・cloud environments・agent internet access）を取得して全行を再検証した。その結果、**ドメイン許可リストはプロキシ有効化なしでは適用されない**こと、`approval_policy = "untrusted"` の廃止、auto-review の既定値と管理キーが判明し、本表と[10章](10-codex.md)・生成ツールを修正した。

| 項目 | 値 | 検証状態 | 確認日 | 出典 |
|---|---|---|---|---|
| `web_search` のモード | `disabled` / `cached` / `indexed` / `live` の4値（旧boolean併存）。`indexed` は検索インデックス承認URLに限る外部取得 | ✅ | 2026-09-23 | [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference) |
| `web_search` 既定値 | `cached`。full accessサンドボックス時は `live` | ✅ | 2026-09-23 | 同上 |
| `web_search` のサーバー承認URL限定検索 | 0.142.0 で告知されたのち、`indexed` として値トークン公開済み | ✅ | 2026-08-04 | 同上 |
| `approval_policy` 値 | `on-request` / `never` / granular テーブル形式（`sandbox_approval` / `rules` / `mcp_elicitations` / `request_permissions` / `skill_approval`）。**`untrusted` は廃止**（設定するとクライアントが起動しないことがある）、`on-failure` は deprecated。厳格な承認はプロジェクトの `trust_level = "untrusted"` で得る。`allowed_approval_policies` の `untrusted` はこの派生ポリシーを許可する値として引き続き有効 | ✅ | 2026-09-23 | 同上 / [agent-approvals-security](https://learn.chatgpt.com/docs/agent-approvals-security) |
| `sandbox_mode` 値 | `read-only` / `workspace-write` / `danger-full-access`。permission profile（`default_permissions`）と併用不可で、`sandbox_mode` がどこかにあると旧方式が優先（管理側 `allowed_permission_profiles` があれば profile を使う） | ✅ | 2026-09-23 | 同上 / [permissions](https://learn.chatgpt.com/docs/permissions) |
| `glob_scan_max_depth` 制約 | 設定時は最低1（Linux・WSL・ネイティブ Windows で deny-read glob の事前展開に使う） | ✅ | 2026-09-23 | 同上 |
| filesystem の特殊パス | `:root`（ルート）/ `:minimal` / `:workspace_roots` / `:tmpdir` / `:slash_tmp`、絶対パス、`~/`。`extends = ":workspace"`＋`":root" = "deny"`＋`":minimal" = "read"` は公式の例と同じ構成。同一パスでは `deny` > `write` > `read`、より具体的なパスが優先 | ✅ | 2026-09-23 | [permissions](https://learn.chatgpt.com/docs/permissions) |
| コマンドネットワークのドメイン許可リスト | `permissions.<name>.network.enabled = true` はプロキシを起動しない。**`features.network_proxy = true`（または管理側 `[experimental_network]` の `enabled = true`）が無いと無制限の直接通信**になり、ドメイン規則は適用されない。プロキシ有効時は allow が無ければ外部宛てを遮断、deny が優先、ローカル／プライベート宛ては既定で遮断。Web検索・Apps・MCP・ブラウザ・Codex cloud・本体通信は対象外 | ✅ | 2026-09-23 | 同上 / [agent-approvals-security](https://learn.chatgpt.com/docs/agent-approvals-security) |
| `[experimental_network]`（requirements） | 管理側からプロキシを起動するネットワーク要件。`enabled` / `domains` / `managed_allowed_domains_only`（管理者の allow のみ有効）等。**experimental で変更され得る。ネイティブ Windows の対応は限定的**。サンドボックスがネットワークを無効にしているときに通信を許可はしない | ✅ | 2026-09-23 | [managed-configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration) |
| 書き込み可能ルート内の保護パス | `.git`（ポインタファイルの参照先を含む）・`.agents`・`.codex` を再帰的に読み取り専用に保護（`workspace-write`／`:workspace`） | ✅ | 2026-09-23 | [agent-approvals-security](https://learn.chatgpt.com/docs/agent-approvals-security) |
| managed requirements の取得失敗時 | 公式記載は**fail-closed方向へ更新**: 有効なキャッシュがあればキャッシュを使用、キャッシュも無く取得失敗ならエラー（黙って非適用起動しない）。旧記載は fail-open。適用バージョン未確認のため実挙動は受入テストで確認 | ✅ | 2026-09-23 | [managed-configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration) |
| `requirements.toml` 主要キー | `allowed_approval_policies` / `allowed_web_search_modes` / `allowed_sandbox_modes` / `allowed_permission_profiles` / `default_permissions` / `allow_remote_control` / `allow_appshots` / `allow_managed_hooks_only` / `[rules].prefix_rules`。追加: `[mcp_servers]`（identity allowlist。空テーブルで全MCP無効）/ `allowed_approvals_reviewers` / `enforce_residency` / `features.plugins` / `[computer_use].allow_locked_computer_use` / `[marketplaces].restrict_to_allowed_sources`。2026-09-23 追加確認: `guardian_policy_config` / `features.guardian_approval` / `[experimental_network]` / `allow_browser_and_computer_use` / `[browser_use]`（`disable_auto_review` 等）/ `[plugins.<p>.mcp_servers]` / `[apps]` / `remote_sandbox_config`。認証系の `allowed_login_methods` / `allowed_chatgpt_workspaces` / `cli_auth_credentials_store` / `chatgpt_base_url` は**ローカルの system requirements か macOS MDM でのみ有効**（クラウド配信では無視）。`[mcp_servers]` の `identity.command` 文字列形式は引数・`cwd`・環境変数を照合しない | ✅ | 2026-09-23 | 同上 |
| 管理 `deny_read` | 絶対パス（glob可）か `~` 始まりで書く（`./` 始まりは不可）。利用者は緩和できず、存在すると full access を拒否する。**ネイティブ Windows ではシェルのサブプロセスによる読み取りには効かない**（直接のファイルツールのみ） | ✅ | 2026-09-23 | 同上 |
| managed requirements 対応バージョン | permission profile 許可リストは 0.138.0 以降（0.137.0 以前は `allowed_permission_profiles`・managed `default_permissions` を無視）。全機能共通の単一最低バージョン記載はなし | ✅ | 2026-09-23 | 同上 |
| Codex web 環境キャッシュ保持時間 | 最大12時間。Business・Enterpriseでは環境にアクセスできる全ユーザーで共有 | ✅ | 2026-09-23 | [cloud environment](https://learn.chatgpt.com/docs/environments/cloud-environment) |
| Secrets の扱い（Codex web） | セットアップスクリプトでのみ利用可。エージェントフェーズ開始前に削除 | ✅ | 2026-09-23 | 同上 |
| Codex web のエージェントフェーズ通信 | 既定オフ。オンにする場合はドメイン許可リスト（None / Common dependencies / All）と許可 HTTP メソッド（`GET`・`HEAD`・`OPTIONS` に限定可）を環境ごとに設定 | ✅ | 2026-09-23 | [internet access](https://learn.chatgpt.com/docs/cloud/internet-access) |
| セッション履歴無効化 | `history.persistence = "save-all" \| "none"`・`history.max_bytes` | ✅ | 2026-09-23 | [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference) |
| 最新安定版 | 0.156.0（2026-09-22） | ✅ | 2026-09-23 | [changelog](https://learn.chatgpt.com/docs/changelog) / [releases](https://github.com/openai/codex/releases) |
| auto-review（Guardian） | 既定は `approvals_reviewer = "user"`（人間が承認）。`"auto_review"` のときだけ、もともと承認が要る操作（サンドボックス外への昇格・ブロックされた通信・書き込み可能ルート外の編集・承認が必要な MCP／App 呼び出し等）を別エージェントが審査。`on-request` か granular のときだけ動き、`never`・full access では承認要求自体が発生しない。審査の構築・実行・解析失敗は fail-closed、タイムアウトでも実行しない。現行のオープンソース実装では1ターンで3回連続または直近50件中10件の拒否でターン中断。管理側は `allowed_approvals_reviewers`・`features.guardian_approval`・`guardian_policy_config`（利用者の `[auto_review].policy` より優先）。0.153.0: Full Access 時は確認のみの操作で審査を省略。0.156.0: 未採点の権限拡大ではキャッシュ済み承認を無効化 | ✅ | 2026-09-23 | [auto-review](https://learn.chatgpt.com/docs/sandboxing/auto-review) / [agent-approvals-security](https://learn.chatgpt.com/docs/agent-approvals-security#automatic-approval-reviews) |
| 信頼済みでないプロジェクト | `trust_level = "untrusted"` のプロジェクトは `.codex/` 配下の設定・Hooks・rules を読み込まない（公式設定リファレンス）。0.150.0 以降はプロジェクト直下の `AGENTS.md` 指示も読み込まない（リリースノートのみ。公式の AGENTS.md ガイドには記載なし）。managed deny-read が権限変更後も維持される修正も 0.150.0 | ✅ | 2026-09-23 | [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference) / [releases](https://github.com/openai/codex/releases) |
| サンドボックス関連の修正 | 0.148.0: deny／読取不能パスで fail-safe。0.151.0: `/cd` でサンドボックス制約を緩められない修正。0.152.0: Windows サンドボックス実行の修正、クラウドタスク要求で未信頼バックエンド URL を拒否。0.155.0: 制限付き WSL サンドボックスからの Windows プロセス経由脱出を遮断、Windows サンドボックスでのファイルシステムルートの read deny に関する変更。0.156.0: Windows オフラインサンドボックスで非ループバックの受信通信を遮断 | ✅ | 2026-09-23 | 同上 / [changelog](https://learn.chatgpt.com/docs/changelog) |
| Hooks の拡張 | 0.148.0: 非同期実行・MCP ツール呼び出しに対応。0.150.0: `Interrupt` Hook 追加。`allow_managed_hooks_only = true` は `requirements.toml` でのみ有効（`config.toml` では無効）。user・project・session・plugin 由来の Hook を飛ばし、managed Hook は残す | ✅ | 2026-09-23 | [releases](https://github.com/openai/codex/releases) / [docs/config.md](https://github.com/openai/codex/blob/main/docs/config.md) |
| プラグイン・マーケットプレイス | 0.146.0〜0.147.0: Agent Plugins マニフェスト・追加マーケットプレイス・ワークスペースからの公開。0.153.0: リモートマーケットプレイスからの CLI インストール。managed 側は `[marketplaces].restrict_to_allowed_sources`・`features.plugins` で制限（OpenAI キュレーションのカタログも許可リストに一致させる必要がある） | ✅ | 2026-09-23 | [releases](https://github.com/openai/codex/releases) |
| MCP 承認の追加保護 | 0.153.0: 記憶した MCP ツール承認をアプリアカウント単位に限定。0.155.0: ローカル TUI での MCP 要求に Touch ID 検証（対応 Mac） | ✅ | 2026-09-21 | 同上 |

## C.2 Claude Code

| 項目 | 値 | 検証状態 | 確認日 | 出典 |
|---|---|---|---|---|
| Bash sandbox 既定read | `~/.aws/credentials`・`~/.ssh/` を**読める**。`denyRead` または `sandbox.credentials.files`（`deny`）で明示遮断が必要。組み込みの資格情報 deny リストは無い | ✅ | 2026-09-21 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| sandbox 対応OS | macOS / Linux / WSL2（ネイティブWindows・WSL1非対応） | ✅ | 2026-09-21 | 同上 |
| `failIfUnavailable` 既定挙動 | 既定 `false`: 警告して**非サンドボックスで継続**（fail-open）。`true`で起動拒否 | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| `autoAllowBashIfSandboxed` 既定値 | **既定 `true`**（auto-allow モード）と settings リファレンスに明記。`false` で regular permissions mode。auto-allow でも `deny`・内容指定 `ask` は効くが bare `Bash` ask はサンドボックス内コマンドでスキップ。`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` 設定時は auto-allow 無効 | ✅ | 2026-09-21 | 同上 |
| `autoAllowBashIfSandboxed` バイパス報告 | **sandbox無効化コマンドの自動承認によるバイパス報告あり**（#29016 は closed、修正バージョン要特定）。#43713（シェル展開を含むコマンドで**過剰にプロンプトが出る**別件）は closed（2026-09-21 確認。close 理由は未表示） | ✅ | 2026-09-21 | [#29016](https://github.com/anthropics/claude-code/issues/29016) / [#43713](https://github.com/anthropics/claude-code/issues/43713) |
| `allowUnsandboxedCommands` | 既定 `true`（サンドボックスで失敗したコマンドを `dangerouslyDisableSandbox` で再実行できる）。`false` で strict sandbox mode。ただし利用者が `!` シェルモードで打つコマンドは v2.1.260 以降 strict でもサンドボックス外（background session と Linux の ENV_SCRUB 設定時を除く） | ✅ | 2026-09-21 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `disableBypassPermissionsMode` | 実在（値 `"disable"`）。**特定バージョンで無効だった実例あり**。#44642 は**修正されないまま closed（not planned）**のため、実効性は受入テストで確認し、効かないバージョンは外部境界で代替。サブエージェント定義の `permissionMode: bypassPermissions` が同キーを無視する抜けは v2.1.223 で修正 | ✅ | 2026-09-21 | [#44642](https://github.com/anthropics/claude-code/issues/44642) / [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| `permissions.defaultMode` の有効スコープ | `auto`・`bypassPermissions` は `.claude/settings.json`・`.claude/settings.local.json` からは効かない（v2.1.257 以降。以前は bypass がどのファイルからも有効）。`manual` は `default` の別名（v2.1.200 以降）。クラウドセッションは `bypassPermissions`・`dontAsk` を設定ファイルから受け付けない | ✅ | 2026-09-21 | [permission-modes](https://code.claude.com/docs/en/permission-modes) |
| 組み込み既定の開始モード | **Pro / Max / Team はターミナル・VS Code 拡張で `auto`**（v2.1.228 以降。ネイティブ Windows は v2.1.233 以降）。Enterprise・Console API キー・`-p`・Agent SDK・Bedrock/Vertex/Foundry/gateway・`disableAutoMode` 設定時・feature flag 取得不可時は `default` | ✅ | 2026-09-21 | 同上 |
| `disableAutoMode` | 値 `"disable"`（トップレベルまたは `permissions` 配下）。`auto` を選択肢から除き、`--permission-mode auto` も `default` で開始。管理配布で稼働中セッションも `default` へ戻る（v2.1.251 以降） | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| `autoMode` 設定ブロック | `environment` / `allow` / `soft_deny` / `hard_deny` / `classifyAllShell`。**user・managed・`--settings` からのみ**読み、project / local は読まない（v2.1.207 以降）。`"$defaults"` を省くと組み込みルールを丸ごと置換。利用者の `allow` は組織の `soft_deny` を上書きできる（`hard_deny` は不可）。`classifyAllShell` は v2.1.193 以降 | ✅ | 2026-09-21 | [auto-mode-config](https://code.claude.com/docs/en/auto-mode-config) |
| `useAutoModeDuringPlan` | 既定 `true`（plan mode でも分類器がコマンドを審査）。`false` は user / local / managed から有効（`.claude/settings.json` からは不可） | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| auto mode 分類器のサーバー側実行 | Enterprise・API・Bedrock/Vertex/Foundry・gateway では v2.1.278 以降サーバー側審査が既定（`CLAUDE_CODE_AUTO_MODE_SERVER=0` で opt-out）。分類器は既定で Sonnet 5。3回連続または累計20回遮断で通常確認へ戻る | ✅ | 2026-09-21 | [permission-modes](https://code.claude.com/docs/en/permission-modes) / [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) |
| `permissions.blockReadsOutsideWorkingDirectories` | v2.1.257 以降。Read/Grep/Glob/LSP の作業ディレクトリ外読み取りを **bypass を含む全モード**で遮断。既知の読み取り Bash コマンドは auto / bypass でも確認。どのスコープの `true` も有効（解除不可）。サンドボックス有効時はホーム配下の読み取りも拒否 | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| `--restricted` | v2.1.248 以降（`CLAUDE_CODE_RESTRICTED=1`）。コマンド実行系ツールと `WebFetch` を除去（`--tools` で名指しした場合を除く）、ファイルツールを作業ディレクトリ内に限定、`bypassPermissions` を拒否、user / project / local 設定ファイルを無視 | ✅ | 2026-09-21 | [cli-reference](https://code.claude.com/docs/en/cli-reference) |
| `sandbox.filesystem.allowRead` | `denyRead` 領域内の再許可。`.` はプロジェクト設定でのみプロジェクトルートに解決 | ✅ | 2026-06-24 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | サブプロセス環境変数からAnthropic・クラウド資格情報を除去 | ✅ | 2026-06-24 | [env-vars](https://code.claude.com/docs/en/env-vars) |
| MCP denylist / モデル固定 | `deniedMcpServers` / `availableModels` / `enforceAvailableModels` | ✅ | 2026-06-24 | [settings](https://code.claude.com/docs/en/settings) |
| `disabledMcpjsonServers` | `.mcp.json` 由来の特定MCPサーバーを名指し拒否（[13.2](13-mcp-plugins-hooks.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| `disableSideloadFlags` | `--mcp-config`・`--plugin-dir`・`--plugin-url`・`--agents` の sideload を起動時に拒否（[13.2](13-mcp-plugins-hooks.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| `disableAllHooks` | 全Hooks＋カスタムstatuslineを無効化（[13.2](13-mcp-plugins-hooks.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| `sandbox.credentials` | スキーマ公開済み: `files: [{path, mode}]`・`envVars: [{name, mode}]`、mode は `"deny"` \| `"mask"`（mask は v2.1.199 以降。egress時にsentinel値を実値へ置換、`injectHosts` で対象ホスト指定。ファイルの mask は v2.1.221 で Linux/WSL 対応）。`allowPlaintextInject` は user/managed/CLI 設定でのみ有効 | ✅ | 2026-08-04 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `sandbox.filesystem.disabled` | v2.1.216 で追加。ネットワーク隔離を残したままファイルシステム隔離のみ無効化。**user / managed / `--settings` でのみ有効**（project からは不可。managed が `sandbox.filesystem` か `credentials.files` の `deny` を設定していると managed のみ）。`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` 設定時は全スコープで無視。機密案件では有効化しない（[11.8](11-claude-code.md)） | ✅ | 2026-09-21 | [sandboxing](https://code.claude.com/docs/en/sandboxing) / [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| `sandbox.network.strictAllowlist` | v2.1.219 で追加。許可リスト外ホストを**確認プロンプトなしで拒否**（未満のバージョンでは無視され確認フローに落ちる）。**有効スコープは user / managed / `--settings` のみ**で、`.claude/settings.json`・`.claude/settings.local.json` に置いても**無効**。サンドボックス内コマンド限定（`WebFetch` は権限ルールに従う） | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) / [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `sandbox.network.tlsTerminate` | v2.1.199 で追加。組み込みプロキシにTLSを終端させ、資格情報マスキング（mask mode）と併用。user / managed / `--settings` でのみ有効。server-managed から配信する場合は利用者の承認ダイアログが必要（v2.1.251 以降） | ✅ | 2026-09-21 | [sandboxing](https://code.claude.com/docs/en/sandboxing) / [server-managed-settings](https://code.claude.com/docs/en/server-managed-settings) |
| auto mode のコマンド単位 `allowed_domains` | v2.1.271 以降。サンドボックス有効な auto mode で、コマンドが必要とするホストを分類器がコマンドと一緒に審査し、そのコマンドの実行中だけ開く。`strictAllowlist` か `allowManagedDomainsOnly` 有効時は拒否される | ✅ | 2026-09-21 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `sandbox.excludedCommands` | 管理側ロック無し（全スコープでマージ）。v2.1.277 で複合コマンドの一部一致で全体が除外される不具合を修正 | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) / [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) |
| `denyRead` の末尾スラッシュ | `"~/.aws/"` のような末尾スラッシュ付き指定は v2.1.224 未満で回避可能だった（修正済み）。本ガイドの例はスラッシュなし | ✅ | 2026-09-21 | [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) |
| `sandbox.allowAppleEvents` | macOSのApple Events許可（既定遮断。有効化で隔離低下。project設定不可） | ✅ | 2026-06-24 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| managed強制キー | `allowManagedReadPathsOnly` / `allowManagedDomainsOnly` / `allowManagedMcpServersOnly` / `allowManagedPermissionRulesOnly` / `allowManagedHooksOnly` / `disableSkillShellExecution` / `disableAutoMode` / `forceRemoteSettingsRefresh` | ✅ | 2026-06-20 | [settings](https://code.claude.com/docs/en/settings) |
| `disableBundledSkills` | バンドルスキル・ワークフローの無効化。`disableWorkflows`（動的ワークフロー無効化）も併存（[11.9](11-claude-code.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| サブエージェント関連の管理キー | `disableAgentView`（background agents・`claude agents`・`--bg`・`/background`・supervisor を無効化）、`disableSideloadFlags`（`--agents`・`--plugin-dir`・`--plugin-url`・`--mcp-config` の sideload を拒否）。**セッション内サブエージェントの個別許可リストは未提供**（[11.9](11-claude-code.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| 出力スタイル／`.claude/rules` の管理キー | `outputStyle` は**選択のみ**。出力スタイルの無効化・制限、`.claude/rules` の制御キーは**未提供**（統制はファイルレビュー＋権限・サンドボックス。[11.9](11-claude-code.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| データ系キー | `enableArtifact`（`false` で無効化。どのスコープからも再有効化不可。**キー自体は v2.1.196 以降**で、ロック挙動とプロジェクト設定での適用は v2.1.242 以降）／ `disableArtifact` は **deprecated** だが `true` は同等扱いのため、古いクライアントが残る環境では併記する／ `disableRemoteControl` / `disableClaudeAiConnectors` / `autoMemoryEnabled` / `cleanupPeriodDays`（既定 30 日） | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| `strictPluginOnlyCustomization` | managed 限定。`true` または `["skills","agents","hooks","mcp"]` の部分集合で、user / project 由来のスキル・カスタムコマンド・サブエージェント・Hooks・MCP を遮断（プラグイン・管理設定・バンドル由来は残る。[11.9](11-claude-code.md)） | ✅ | 2026-09-21 | 同上 |
| プラグイン供給元の管理キー | `strictKnownMarketplaces`（空配列で全面禁止）／ `blockedMarketplaces`（`owner/*` は v2.1.223 以降）／ `disableCommandPluginSources`（v2.1.229 以降。`allowManagedHooksOnly` 有効時は既定で禁止）／ npm ソースは v2.1.275 以降 `--ignore-scripts` で取得 | ✅ | 2026-09-21 | 同上 / [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) |
| HTTP Hooks の管理キー | `allowedHttpHookUrls`（空配列で全面遮断。全スコープでマージ、managed 由来 Hook にも適用）／ `httpHookAllowedEnvVars`。managed 側が読めないときは v2.1.267 以降「何も許可しない」 | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| MCP 配布・許可リストの変更 | v2.1.259 以降 `allowedMcpServers` は利用者追加サーバーのみ対象（`managed-mcp.json` のサーバーは絞られない。止めるには `deniedMcpServers`）。`managedMcpServers`（HTTP/SSE の組織配布）は v2.1.259 以降 | ✅ | 2026-09-21 | 同上 |
| セッション間メッセージ | v2.1.224 以降 `SendMessage` / `ListAgents`。`crossSessionInbound`（`accept` / `hold` / `refuse`。project / local はより厳しい値のみ有効。managed の不正値は `refuse` 扱い）／ `isolatePeerMachines`（他マシンへの送信前に承認。bypass でも有効）。auto mode では送信内容も分類器が審査（v2.1.222 以降） | ✅ | 2026-09-21 | 同上 / [permission-modes](https://code.claude.com/docs/en/permission-modes) |
| Remote Control | `disableRemoteControl`。リポジトリ設定からは自動起動を有効化できない（v2.1.222 以降）。Team/Enterprise は管理コンソールで組織単位に無効化可 | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) / [managed-settings](https://code.claude.com/docs/en/managed-settings) |
| `AGENTS.md` の読み込み | v2.1.277 以降、`CLAUDE.md` の無いプロジェクトでは `AGENTS.md` を読む（Bedrock/Vertex/Foundry は未対応）。managed の `claudeMd` で組織共通指示を配布可（承認ダイアログ不要。v2.1.260 以降） | ✅ | 2026-09-21 | [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) / [server-managed-settings](https://code.claude.com/docs/en/server-managed-settings) |
| `requiredMinimumVersion` / `requiredMaximumVersion` | 許可バージョン範囲外のクライアント起動を拒否（managed 限定。v2.1.163 以降。`claude update` / `claude doctor` は下限未満でも動く） | ✅ | 2026-09-21 | [settings-reference](https://code.claude.com/docs/en/settings-reference) |
| 下限バージョンの目安（セキュリティ修正） | v2.1.222: `PreToolUse` の allow がバックグラウンドタスクのツール制限を迂回する不具合修正。v2.1.223: Bash 権限チェックのコマンド隠蔽バイパス修正、サブエージェント定義の bypass 抜け修正。v2.1.224: `denyRead` 末尾スラッシュ回避の修正。v2.1.232: Linux サンドボックスの保護パス迂回の hardening、PowerShell／Windows の権限バイパス修正。v2.1.233〜234: Windows NT パス（`\??\`）経由の NTLM 資格情報漏えい経路の遮断。v2.1.236: macOS のワイルドカード read-deny の優先順位修正。v2.1.251: 権限確認後のシンボリックリンク差し替え（TOCTOU）修正、project 設定からの詳細トレース有効化を遮断。v2.1.259: 管理設定の解析失敗時に起動拒否。v2.1.268: シンボリックリンク経由ディレクトリの deny 不適用修正 | ✅ | 2026-09-21 | [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) |
| セッション永続化無効化 | `--no-session-persistence` は **print mode（`-p`）のみ有効**。全モード（対話含む）は環境変数 `CLAUDE_CODE_SKIP_PROMPT_HISTORY`（フラグより優先） | ✅ | 2026-09-21 | [cli-reference](https://code.claude.com/docs/en/cli-reference) |
| 管理設定の配布パス | macOS `/Library/Application Support/ClaudeCode/`、Linux/WSL `/etc/claude-code/`、Windows `C:\Program Files\ClaudeCode\`（`managed-settings.json`・`managed-settings.d/`・`managed-mcp.json`）。旧 `C:\ProgramData\ClaudeCode\` は読まれない。Windows は `HKLM\SOFTWARE\Policies\ClaudeCode` の `Settings` 値も可。MDM/ファイルは起動時読込＋30分ごとに変更確認 | ✅ | 2026-09-21 | [managed-settings](https://code.claude.com/docs/en/managed-settings) |
| 管理設定の解析失敗・不正エントリ | JSON として解析できない管理ファイル／plist／HKLM 値があると**起動拒否**（v2.1.259 以降）。個別エントリのスキーマ違反は当該キーだけ除去。`allowManagedHooksOnly`・`allowManagedMcpServersOnly` は不正値のとき `true` 扱い、`allowedHttpHookUrls` 等は「何も許可しない」に倒れる（v2.1.267 以降） | ✅ | 2026-09-21 | 同上 |
| server-managed settings の取得失敗時 | 既定 **fail-open**（キャッシュがあればキャッシュ、無ければ管理設定なしで起動し対話セッションで警告）。`forceRemoteSettingsRefresh: true` で fail-closed（`claude auth` 系は除外）。毎時の再取得は常に fail-open。シェルで `CLAUDE_CODE_USE_*` や独自 `ANTHROPIC_BASE_URL` をエクスポートすると**取得自体がスキップ**。公式に「クライアント側統制であり境界ではない。非管理端末では管理者権限なしに回避可能」と明記 | ✅ | 2026-09-21 | [server-managed-settings](https://code.claude.com/docs/en/server-managed-settings) |
| server-managed settings の承認ダイアログ | Hooks・シェル実行系キー・サンドボックスバイナリ指定・サンドボックスを弱める／TLS 終端／独自プロキシ／資格情報注入のキー・一部 `env` 変数は利用者の承認後に適用（拒否すると終了）。v2.1.251 以前はサンドボックス系が無承認で適用されていた。`-p` では承認記録なしにその実行だけ適用 | ✅ | 2026-09-21 | 同上 |

> [!NOTE]
> `autoAllowBashIfSandboxed` の既定値は、2026-09-21 に公式 settings リファレンスで **`true`** と確認した（2026-08-04 時点では明示が見当たらなかった）。既定のままでは「サンドボックス有効＝Bash 自動承認」になるため、本ガイドは引き続き**明示的に `false`（regular permissions mode）を推奨**する（[11.4](11-claude-code.md)）。

> [!IMPORTANT]
> 2026-09-21 の確認で、**設定キーの有効スコープ**が値と同じくらい重要であることが分かった。`strictAllowlist`・`tlsTerminate`・`filesystem.disabled`・`autoMode`・`useAutoModeDuringPlan`・`defaultMode` の `auto`／`bypassPermissions` は、リポジトリの `.claude/settings.json` に置いても無視される。公式の settings リファレンス（Scope 列）で各キーの有効スコープを確認し、user / managed に置くべきキーをプロジェクト設定に置かない。

## C.3 契約プランと強制機能の対応

| 強制機能 | 個人系 | チーム・ビジネス系 | 検証状態 |
|---|---|---|---|
| Codex managed requirements | × | ○ | ⚠️ プラン名・適用範囲は要確認（クラウド配信の requirements は ChatGPT Business・Enterprise が対象と公式に記載。2026-09-23 確認） |
| Claude Code managed settings | × | ○ | ⚠️ 同上 |
| 組織監査ログ | × | ○ | ⚠️ 同上 |

> [!IMPORTANT]
> プラン名（Plus/Pro/Team/Business/Enterprise等）と、各プランで利用できる管理・監査機能の対応は変動が大きい。**導入時に必ず最新の契約条件・管理者ドキュメントで確認**し、本表の検証状態を✅へ更新すること。「×」のプランで上位レベルを実施する場合の代替は[06.2](06-quick-reference.md)を参照。

[← 目次へ戻る](README.md)
