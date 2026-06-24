# 付録C 揮発値一覧（バージョン・既定値・設定キー）

[← 目次へ戻る](README.md)

本文中の「変動しやすい具体値」をここに集約する。製品更新時は**本表だけを洗い、確認日を更新**すればよい（[17.2](17-periodic-review.md)）。本文の設定例コードブロックは各製品章に残してある。

- **基準確認日**: 2026-06-20
- **検証状態**の凡例: ✅ 一次資料（公式ドキュメント／GitHub）で確認済み ／ ⚠️ 本ガイド作成時点で未再検証（旧版記述を引き継ぎ。導入時に要確認）

## C.1 Codex

| 項目 | 値 | 検証状態 | 確認日 | 出典 |
|---|---|---|---|---|
| `web_search` のモード | `disabled` / `cached` / `live`（旧boolean併存） | ✅ | 2026-06-20 | [config-reference](https://developers.openai.com/codex/config-reference) |
| `web_search` 既定値 | `cached`。full accessサンドボックス時は `live` | ✅ | 2026-06-20 | 同上 |
| `approval_policy` 値 | `untrusted` / `on-request` / `never` | ✅ | 2026-06-20 | 同上 |
| `sandbox_mode` 値 | `read-only` / `workspace-write` / `danger-full-access` | ✅ | 2026-06-20 | 同上 |
| `glob_scan_max_depth` 制約 | 設定時は最低1 | ✅ | 2026-06-20 | 同上 |
| managed requirements の取得失敗時 | **fail-open**（管理要件なしで起動継続） | ✅ | 2026-06-20 | [managed-configuration](https://developers.openai.com/codex/enterprise/managed-configuration) |
| `requirements.toml` 主要キー | `allowed_approval_policies` / `allowed_web_search_modes` / `allowed_sandbox_modes` / `allowed_permission_profiles` / `default_permissions` / `allow_remote_control` / `allow_appshots` / `allow_managed_hooks_only` / `[rules].prefix_rules` | ✅ | 2026-06-20 | 同上 |
| managed requirements 対応バージョン | 0.138.0以降（要再確認） | ⚠️ | — | 導入時に[admin-setup](https://developers.openai.com/codex/enterprise/admin-setup)で確認 |
| Codex web 環境キャッシュ保持時間 | 最大12時間／Business・Enterpriseで共有され得る（要再確認） | ⚠️ | — | [cloud/environments](https://developers.openai.com/codex/cloud/environments) |
| セッション履歴無効化 | `history.persistence = "none"`（要再確認） | ⚠️ | — | [config-reference](https://developers.openai.com/codex/config-reference) |

## C.2 Claude Code

| 項目 | 値 | 検証状態 | 確認日 | 出典 |
|---|---|---|---|---|
| Bash sandbox 既定read | `~/.aws/credentials`・`~/.ssh/` を**読める**。`denyRead`で明示遮断が必要 | ✅ | 2026-06-20 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| sandbox 対応OS | macOS / Linux / WSL2（ネイティブWindows・WSL1非対応） | ✅ | 2026-06-20 | 同上 |
| `failIfUnavailable` 既定挙動 | 未設定時は警告して**非サンドボックスで継続**（fail-open）。`true`で起動拒否 | ✅ | 2026-06-20 | 同上 |
| `autoAllowBashIfSandboxed` | 実在。auto-allowでpermission modeに関わらず自動承認され得る。**シェル展開・sandbox無効化コマンドによるバイパス報告あり** | ✅ | 2026-06-20 | [#29016](https://github.com/anthropics/claude-code/issues/29016) / [#43713](https://github.com/anthropics/claude-code/issues/43713) |
| `disableBypassPermissionsMode` | 実在（値 `"disable"`）。**特定バージョンで無効だった実例あり** | ✅ | 2026-06-20 | [#44642](https://github.com/anthropics/claude-code/issues/44642) |
| `sandbox.filesystem.allowRead` | `denyRead` 領域内の再許可。`.` はプロジェクト設定でのみプロジェクトルートに解決 | ✅ | 2026-06-24 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | サブプロセス環境変数からAnthropic・クラウド資格情報を除去 | ✅ | 2026-06-24 | [env-vars](https://code.claude.com/docs/en/env-vars) |
| `sandbox.credentials` | 資格情報ファイル＋シークレット環境変数の読取を一括ブロック（CHANGELOG報告。要正式確認） | ⚠️ | — | 導入時に[settings](https://code.claude.com/docs/en/settings)で確認 |
| managed強制キー | `allowManagedReadPathsOnly` / `allowManagedDomainsOnly` / `allowManagedMcpServersOnly` / `allowManagedPermissionRulesOnly` / `allowManagedHooksOnly` / `disableSkillShellExecution` / `disableAutoMode` / `forceRemoteSettingsRefresh` | ✅ | 2026-06-20 | [settings](https://code.claude.com/docs/en/settings) |
| データ系キー | `disableArtifact` / `disableRemoteControl` / `disableClaudeAiConnectors` / `autoMemoryEnabled` / `cleanupPeriodDays` | ✅ | 2026-06-20 | 同上 |
| セッション永続化無効化 | `--no-session-persistence` 等（要再確認） | ⚠️ | — | 導入時に[settings](https://code.claude.com/docs/en/settings)で確認 |

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
