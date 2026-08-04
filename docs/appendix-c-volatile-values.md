# 付録C 揮発値一覧（バージョン・既定値・設定キー）

[← 目次へ戻る](README.md)

本文中の「変動しやすい具体値」をここに集約する。製品更新時は**本表だけを洗い、確認日を更新**すればよい（[17.2](17-periodic-review.md)）。本文の設定例コードブロックは各製品章に残してある。

- **基準確認日**: 2026-08-04
- **検証状態**の凡例: ✅ 一次資料（公式ドキュメント／GitHub）で確認済み ／ ⚠️ 本ガイド作成時点で未再検証（旧版記述を引き継ぎ。導入時に要確認）

## C.1 Codex

> [!NOTE]
> `developers.openai.com/codex` 配下のドキュメントは `learn.chatgpt.com/docs` 配下へ恒久移転している（308リダイレクトを 2026-08-04 に確認）。旧URLもリダイレクトで到達できる。本表の出典は移転先を確認できたものから新URLへ更新している。

| 項目 | 値 | 検証状態 | 確認日 | 出典 |
|---|---|---|---|---|
| `web_search` のモード | `disabled` / `cached` / `indexed` / `live` の4値（旧boolean併存）。`indexed` は検索インデックス承認URLに限る外部取得 | ✅ | 2026-08-04 | [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference) |
| `web_search` 既定値 | `cached`。full accessサンドボックス時は `live` | ✅ | 2026-08-04 | 同上 |
| `web_search` のサーバー承認URL限定検索 | 0.142.0 で告知されたのち、`indexed` として値トークン公開済み | ✅ | 2026-08-04 | 同上 |
| `approval_policy` 値 | `untrusted` / `on-request` / `never`。加えて granular テーブル形式（`sandbox_approval` / `rules` / `mcp_elicitations` / `request_permissions` / `skill_approval`）が追加（導入バージョン未確認） | ✅ | 2026-08-04 | 同上 |
| `sandbox_mode` 値 | `read-only` / `workspace-write` / `danger-full-access` | ✅ | 2026-06-20 | 同上 |
| `glob_scan_max_depth` 制約 | 設定時は最低1 | ✅ | 2026-06-20 | 同上 |
| filesystem の `:root` トークン | **現行 config-reference に掲載なし**（特殊トークンは `:minimal` / `:workspace_roots` のみ記載。削除か改称かは未確認）。`:root` deny を使う設定は対象バージョンでの有効性を導入時に確認 | ⚠️ | 2026-08-04 | [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference) |
| managed requirements の取得失敗時 | 公式記載は**fail-closed方向へ更新**: 有効なキャッシュがあればキャッシュを使用、キャッシュも無く取得失敗ならエラー（黙って非適用起動しない）。旧記載は fail-open。適用バージョン未確認のため実挙動は受入テストで確認 | ✅ | 2026-08-04 | [managed-configuration](https://learn.chatgpt.com/docs/enterprise/managed-configuration) |
| `requirements.toml` 主要キー | `allowed_approval_policies` / `allowed_web_search_modes` / `allowed_sandbox_modes` / `allowed_permission_profiles` / `default_permissions` / `allow_remote_control` / `allow_appshots` / `allow_managed_hooks_only` / `[rules].prefix_rules`。追加: `[mcp_servers]`（identity allowlist。空テーブルで全MCP無効）/ `allowed_approvals_reviewers` / `enforce_residency` / `features.plugins` / `[computer_use].allow_locked_computer_use` / `[marketplaces].restrict_to_allowed_sources` | ✅ | 2026-08-04 | 同上 |
| managed requirements 対応バージョン | permission profile 許可リストは 0.138.0 以降（0.137.0 以前は `allowed_permission_profiles`・managed `default_permissions` を無視）。全機能共通の単一最低バージョン記載はなし | ✅ | 2026-08-04 | 同上 |
| Codex web 環境キャッシュ保持時間 | 最大12時間。Business・Enterpriseでは環境にアクセスできる全ユーザーで共有 | ✅ | 2026-08-04 | [cloud environment](https://learn.chatgpt.com/docs/environments/cloud-environment) |
| Secrets の扱い（Codex web） | セットアップスクリプトでのみ利用可。エージェントフェーズ開始前に削除 | ✅ | 2026-08-04 | 同上 |
| セッション履歴無効化 | `history.persistence = "save-all" \| "none"`・`history.max_bytes` | ✅ | 2026-08-04 | [config-reference](https://learn.chatgpt.com/docs/config-file/config-reference) |

## C.2 Claude Code

| 項目 | 値 | 検証状態 | 確認日 | 出典 |
|---|---|---|---|---|
| Bash sandbox 既定read | `~/.aws/credentials`・`~/.ssh/` を**読める**。`denyRead`で明示遮断が必要 | ✅ | 2026-06-20 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| sandbox 対応OS | macOS / Linux / WSL2（ネイティブWindows・WSL1非対応） | ✅ | 2026-06-20 | 同上 |
| `failIfUnavailable` 既定挙動 | 未設定時は警告して**非サンドボックスで継続**（fail-open）。`true`で起動拒否 | ✅ | 2026-06-20 | 同上 |
| `autoAllowBashIfSandboxed` | 実在。auto-allowでpermission modeに関わらず自動承認され得る。**sandbox無効化コマンドの自動承認によるバイパス報告あり**（#29016 は closed、修正バージョン要特定）。#43713 は open のまま（2026-08-04 再確認）。シェル展開を含むコマンドで**過剰にプロンプトが出る**挙動の報告であり、バイパスではない | ✅ | 2026-08-04 | [#29016](https://github.com/anthropics/claude-code/issues/29016) / [#43713](https://github.com/anthropics/claude-code/issues/43713) |
| `disableBypassPermissionsMode` | 実在（値 `"disable"`）。**特定バージョンで無効だった実例あり**。#44642 は**修正されないまま closed（not planned）**のため、実効性は受入テストで確認し、効かないバージョンは外部境界で代替 | ✅ | 2026-08-04 | [#44642](https://github.com/anthropics/claude-code/issues/44642) |
| `sandbox.filesystem.allowRead` | `denyRead` 領域内の再許可。`.` はプロジェクト設定でのみプロジェクトルートに解決 | ✅ | 2026-06-24 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | サブプロセス環境変数からAnthropic・クラウド資格情報を除去 | ✅ | 2026-06-24 | [env-vars](https://code.claude.com/docs/en/env-vars) |
| MCP denylist / モデル固定 | `deniedMcpServers` / `availableModels` / `enforceAvailableModels` | ✅ | 2026-06-24 | [settings](https://code.claude.com/docs/en/settings) |
| `disabledMcpjsonServers` | `.mcp.json` 由来の特定MCPサーバーを名指し拒否（[13.2](13-mcp-plugins-hooks.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| `disableSideloadFlags` | `--mcp-config`・`--plugin-dir`・`--plugin-url`・`--agents` の sideload を起動時に拒否（[13.2](13-mcp-plugins-hooks.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| `disableAllHooks` | 全Hooks＋カスタムstatuslineを無効化（[13.2](13-mcp-plugins-hooks.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| `sandbox.credentials` | スキーマ公開済み: `files: [{path, mode}]`・`envVars: [{name, mode}]`、mode は `"deny"` \| `"mask"`（mask は v2.1.199 以降。egress時にsentinel値を実値へ置換、`injectHosts` で対象ホスト指定。ファイルの mask は v2.1.221 で Linux/WSL 対応）。`allowPlaintextInject` は user/managed/CLI 設定でのみ有効 | ✅ | 2026-08-04 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `sandbox.filesystem.disabled` | v2.1.216 で追加。ネットワーク隔離を残したままファイルシステム隔離のみ無効化。機密案件では有効化しない（[11.8](11-claude-code.md)） | ✅ | 2026-08-04 | [sandboxing](https://code.claude.com/docs/en/sandboxing) / [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) |
| `sandbox.network.strictAllowlist` | v2.1.219 で追加。許可リスト外ホストを**確認プロンプトなしで拒否**（未満のバージョンでは無視され確認フローに落ちる） | ✅ | 2026-08-04 | [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) |
| `sandbox.network.tlsTerminate` | v2.1.199 で追加。組み込みプロキシにTLSを終端させ、資格情報マスキング（mask mode）と併用 | ✅ | 2026-08-04 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `sandbox.allowAppleEvents` | macOSのApple Events許可（既定遮断。有効化で隔離低下。project設定不可） | ✅ | 2026-06-24 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| managed強制キー | `allowManagedReadPathsOnly` / `allowManagedDomainsOnly` / `allowManagedMcpServersOnly` / `allowManagedPermissionRulesOnly` / `allowManagedHooksOnly` / `disableSkillShellExecution` / `disableAutoMode` / `forceRemoteSettingsRefresh` | ✅ | 2026-06-20 | [settings](https://code.claude.com/docs/en/settings) |
| `disableBundledSkills` | バンドルスキル・ワークフローの無効化。`disableWorkflows`（動的ワークフロー無効化）も併存（[11.9](11-claude-code.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| サブエージェント関連の管理キー | `disableAgentView`（background agents・`claude agents`・`--bg`・`/background`・supervisor を無効化）、`disableSideloadFlags`（`--agents`・`--plugin-dir`・`--plugin-url`・`--mcp-config` の sideload を拒否）。**セッション内サブエージェントの個別許可リストは未提供**（[11.9](11-claude-code.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| 出力スタイル／`.claude/rules` の管理キー | `outputStyle` は**選択のみ**。出力スタイルの無効化・制限、`.claude/rules` の制御キーは**未提供**（統制はファイルレビュー＋権限・サンドボックス。[11.9](11-claude-code.md)） | ✅ | 2026-06-30 | [settings](https://code.claude.com/docs/en/settings) |
| データ系キー | `disableArtifact` / `disableRemoteControl` / `disableClaudeAiConnectors` / `autoMemoryEnabled` / `cleanupPeriodDays` | ✅ | 2026-06-20 | 同上 |
| `requiredMinimumVersion` / `requiredMaximumVersion` | 許可バージョン範囲外のクライアント起動を拒否 | ✅ | 2026-06-24 | [settings](https://code.claude.com/docs/en/settings) |
| セッション永続化無効化 | `--no-session-persistence` は **print mode（`-p`）のみ有効**。全モード（対話含む）は環境変数 `CLAUDE_CODE_SKIP_PROMPT_HISTORY`（フラグより優先） | ✅ | 2026-08-04 | [cli-reference](https://code.claude.com/docs/en/cli-reference) |

> [!NOTE]
> `autoAllowBashIfSandboxed` の**既定値**は、公式settingsリファレンスに明示が見当たらなかった。本ガイドは既定値を断定せず、**明示的に `false`（regular permissions mode相当）を推奨**する立場をとる（[11.4](11-claude-code.md)）。

## C.3 契約プランと強制機能の対応

| 強制機能 | 個人系 | チーム・ビジネス系 | 検証状態 |
|---|---|---|---|
| Codex managed requirements | × | ○ | ⚠️ プラン名・適用範囲は要確認 |
| Claude Code managed settings | × | ○ | ⚠️ 同上 |
| 組織監査ログ | × | ○ | ⚠️ 同上 |

> [!IMPORTANT]
> プラン名（Plus/Pro/Team/Business/Enterprise等）と、各プランで利用できる管理・監査機能の対応は変動が大きい。**導入時に必ず最新の契約条件・管理者ドキュメントで確認**し、本表の検証状態を✅へ更新すること。「×」のプランで上位レベルを実施する場合の代替は[06.2](06-quick-reference.md)を参照。

[← 目次へ戻る](README.md)
