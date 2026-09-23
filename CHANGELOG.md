# Changelog

本リポジトリ（セキュリティ・運用ガイド `docs/` と生成ツール `generator/`）の変更履歴。

- [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) のカテゴリ（Added / Changed 等）を借りつつ、**日付見出し（`## YYYY-MM-DD`）の逆年代ログ**として運用する（リリース・版番号の概念は持たない）。
- 更新手順は `AGENTS.md`「CHANGELOG の運用」を参照。ユーザーの指示で更新する。

## 2026-09-23

### Added
- docs/11: auto mode（分類器）の位置づけと統制を 11.10 として新設。セッション間メッセージ・Remote Control・バックグラウンドエージェントの統制を 11.11 として新設。
- docs: 新しい統制キーを記載: `permissions.blockReadsOutsideWorkingDirectories`（v2.1.257 以降）、`--restricted`（v2.1.248 以降）、`strictPluginOnlyCustomization`、`strictKnownMarketplaces` / `blockedMarketplaces` / `disableCommandPluginSources`、HTTP Hooks の `allowedHttpHookUrls` / `httpHookAllowedEnvVars`、`managedMcpServers`、`crossSessionInbound` / `isolatePeerMachines`（docs/11・13・付録C）。
- docs/12: 承認の自動審査（Codex auto-review ↔ Claude Code auto mode）、指示・拡張の供給元固定、セッション間連携・遠隔操作の対応行を追加。
- docs/15: 受入テストに `strictAllowlist` の配置、開始モード、作業ディレクトリ外読み取りの遮断、セッション間メッセージの拒否、Codex auto-review の観点を追加。docs/16・17・付録A にも対応する確認項目・記入欄を追加。
- generator: L3 以上の `managed-settings.json` に `crossSessionInbound: "refuse"` と `isolatePeerMachines: true` を出力（docs/11 11.5・11.11 と一致）。
- generator: 生成する受入チェックリストに製品別の追加行を出力する `agentsec/checklist.py` を追加（docs/15 の追加観点を Claude Code 向け4行・Codex 向け1行として反映）。
- generator: `selfcheck.py` が project settings 内の `strictAllowlist` / `tlsTerminate` / `filesystem.disabled`（user / managed でのみ有効なキー）を検出したとき WARN。
- generator: `selfcheck.py` が Codex のドメイン許可リストをプロキシ無しで使う設定（config.toml で `features.network_proxy` 無し、requirements.toml で `[experimental_network]` 無し）を FAIL、絶対パスでも `~` 始まりでもない `deny_read` を WARN にする。受入チェックリストの Codex 行にプロキシ込みの実拒否確認を追加（Codex 向け2行）。
- docs: 10.4 に `network.enabled` と `features.network_proxy` の組み合わせごとの挙動表、10.5 に `[experimental_network]` の設定例と注意、16.4・17・15 にプロキシ有効化の確認項目を追加。
- docs/03: 3.2「プロンプトインジェクションは防げない前提で設計する」を新設。非信頼入力・機密データ・外部送信の3要素を1セッションで同時に成立させない原則（lethal trifecta／Agents Rule of Two）を製品非依存の SHOULD として記載し、docs/05・16・19 から参照。
- docs/03: リスク表に「エージェントCLIの悪用」「MCP経由の注入・権限濫用」「メモリ汚染」「無人実行・CIでの悪用」を追加。Nx「s1ngularity」事件（2025-08）を事例として記載し、3.3 に OWASP Top 10 for Agentic Applications 2026 との対応表を追加。
- docs/04: 実行構成に 4.4「ベンダーのクラウド環境で動くエージェント」と 4.5「CI・スケジュール実行など無人で動くエージェント」を追加（既存の 4.4・4.5 は 4.6・4.7 へ繰り下げ）。docs/05 に「無人実行の扱い」を追加。
- docs/14: 14.4「CI上でエージェントを動かす場合」を新設（起動できる人の限定、`pull_request_target`、トークン権限、シェルへの直接展開の禁止、使い捨てランナー、公式 Action の既定）。
- docs/07: 7.4「依存パッケージの追加」を新設。slopsquatting への対策と、npm・pnpm・Yarn・Bun・uv・pip のクールダウン設定（設定名・単位・既定・導入版）を各公式ドキュメントで確認して記載。
- docs/08: 8.7「エージェント自身とホスト上のツールの資格情報」を新設（GitHub CLI・`~/.npmrc`・`~/.docker/config.json`・エージェントのログイン情報等。ログイン済みのエージェントCLIが悪用される経路と対策）。
- docs/13: 13.4「MCP特有の脅威」を新設（ツール定義への指示埋め込み、承認後の定義変更、実行結果経由の注入、ツール名の衝突、token passthrough、ローカルMCPの実行権限）。
- docs/02: 2.7 に自動メモリ・永続メモリ（メモリ汚染）を追加。
- docs/20: 「AIエージェントのセキュリティ（製品非依存）」「事例」「CI・依存パッケージ」の節を追加（OWASP、MCP Security Best Practices、NIST SP 800-218A、AI事業者ガイドライン第1.2版等）。

### Changed
- docs: 2026-08-04 以降の Claude Code の更新を一次資料（settings reference・sandboxing・permission modes・managed settings・server-managed settings・CHANGELOG v2.1.278 まで）で確認し反映。
  - Pro / Max / Team では v2.1.228 以降、ターミナルと VS Code 拡張の組み込み既定の開始モードが `auto`。推奨（L1 `plan`／L2 以上 `default`）を維持するため `permissions.defaultMode` を明示する旨を 11.2・11.4 に記載。VS Code 拡張はプロジェクト設定を開始モードの決定に使わないため、ユーザー設定または管理設定に置く。
  - `autoAllowBashIfSandboxed` の既定値が `true` と公式に明記されたことを反映（明示 `false` 推奨は維持。付録C の「既定値は明示なし」注記を差し替え）。
  - 設定キーの有効スコープを付録C に記録: `strictAllowlist`・`tlsTerminate`・`filesystem.disabled`・`autoMode`・`useAutoModeDuringPlan`、および `defaultMode` の `auto` / `bypassPermissions` はリポジトリの `.claude/settings.json` から効かない。
  - server-managed settings は既定 fail-open で、プロバイダ環境変数や独自 `ANTHROPIC_BASE_URL` のエクスポートで取得自体がスキップされる点、管理設定ファイルの解析失敗時は起動拒否（v2.1.259 以降）となる点、サンドボックスを弱める配信設定は承認ダイアログを要する点（v2.1.251 以降）を 11.5・付録C に記載。`requiredMinimumVersion` の下限根拠としてセキュリティ修正の一覧を付録C に追加。
  - `disableArtifact` は deprecated。docs/11 11.5 と generator は `enableArtifact: false` を正としつつ、同キーを認識しない v2.1.196 未満のクライアント向けに `disableArtifact: true` を併記。
  - Issue #44642（closed, not planned）・#43713（closed）を再確認。
- docs/10・付録C: Codex は公式リファレンス（`learn.chatgpt.com`）へ作業環境から到達できなかったため、設定リファレンス由来の値は 2026-08-04 確認のまま据え置き。GitHub リリース（0.143.0〜0.155.1）と `docs/config.md` で確認できた事項（auto-review（Guardian）、信頼済みでないプロジェクトの `AGENTS.md` 非読込、サンドボックス関連修正、Hooks の非同期・MCP 呼び出し対応、プラグインマーケットプレイス、`allow_managed_hooks_only` は `requirements.toml` でのみ有効）を追記。→ 同日、下記のとおり公式ドキュメントで再検証した。
- 付録C の基準確認日を 2026-08-04 から 2026-09-21（Claude Code）に更新（Codex 設定リファレンスは 2026-08-04 のまま）。`docs/README.md` の仕様確認基準日も同様に併記へ変更。→ 同日の再検証で Codex も 2026-09-23 に更新した（下記）。
- docs/00 R3・R5、docs/02 2.7、docs/08 に自動承認レビュー・有効スコープ・`sandbox.credentials` の観点を追記。docs/20 に参照リンクを追加。
- docs/10・付録C: Codex の値を公式ドキュメント（`learn.chatgpt.com` の config-reference・managed-configuration・permissions・agent-approvals-security・auto-review・cloud environments・agent internet access）で再検証し、付録C.1 の全行を 2026-09-23 付で更新（⚠️ は解消）。
  - `approval_policy = "untrusted"` は廃止（`on-failure` は deprecated）。`allowed_approval_policies` の `untrusted` は `trust_level = "untrusted"` 由来の厳格な承認を許可する値として有効なため、10.5 と generator の値は維持し注記を追加。10.8 の避ける設定に追加。
  - auto-review は既定 `approvals_reviewer = "user"`。管理側は `allowed_approvals_reviewers`・`features.guardian_approval`・`guardian_policy_config` で制御できる（旧記載の「無効化キーなし」を訂正）。審査失敗は fail-closed、タイムアウトでも実行しない点を記載。公式 URL の移転に合わせて docs/20 を更新。
  - filesystem の `:root` は公式の Permissions ページに記載された特殊パスで、本ガイドの構成は公式の例と同じ（10.4 の要確認注記を差し替え）。書き込み保護パスに `.agents` を追記。
  - 管理 `deny_read` の書式（絶対パスか `~` 始まり）と、ネイティブ Windows ではシェルのサブプロセスに効かない制約、Codex web のエージェント通信設定、追加の管理キー、最新安定版 0.156.0 を付録C に記録。
- 付録C の基準確認日（Codex）を 2026-08-04 から 2026-09-23 に更新。`docs/README.md` の仕様確認基準日も同様。
- generator: 生成物 README の Claude Code 適用手順を拡充。`strictAllowlist` と `defaultMode` の置き場所を、管理設定が生成物に含まれるか（チーム系かつ L3 以上）に応じて `~/.claude/settings.json` または同梱の `managed-settings.json` へ案内。
- docs: 製品非依存層（08・13・15・16・17）に混在していた Claude Code／Codex 固有の設定キーを「製品別の実装例」として本文の統制目標から分離。節番号は generator・付録C からの参照のため維持。
- docs/README: 12章を製品固有層（非依存層と2製品の橋渡し）に分類し直し、層分類の表と目次の不一致を解消。
- docs/19: 判断基準に3要素の同時成立と無人実行の2問を追加（一般19問＋本ガイド固有2問）。
- docs/14・17・付録B: エージェント由来の変更のレビューを依頼者以外が行う等の Git 運用、インシデント時のエージェント固有の失効・保全・除去手順、利用者ルール（権限スキップのエイリアス禁止、依存パッケージの実在確認）を追加。付録A に実行形態と無人実行の記入欄を追加。

### Fixed
- generator: Codex の `requirements.toml` の `deny_read` を絶対パスの glob（例: `/**/.env`）で出力する。管理 `deny_read` は絶対パスか `~` 始まりが公式の書式で、従来の相対 glob（`**/.env`）は公式の例にない形だった。
- generator: 生成する project `settings.json` から `sandbox.network.strictAllowlist` を除去。同キーは user / managed / `--settings` でのみ有効で、リポジトリの `.claude/settings.json` に置いても無視される（docs/11 11.4 の設定例も同様に修正。設定の存在と実効性が一致していなかった）。
- generator: `selfcheck.py` が `autoAllowBashIfSandboxed` 未指定を安全側とみなしていた前提を修正。既定は `true`（auto-allow）のため、`enabled` の有無に関わらず未指定を FAIL とし、`managed-settings.json` も検査対象に加えた。
- docs/06: 6.3 の「最右行」を「最下行」に修正。
- docs/15: Issue #44642 の確認日を docs/00 と同じ 2026-09-21 に揃えた。

### Security
- generator・docs/10: Codex のドメイン許可リストが適用されず、サンドボックス内コマンドが無制限に直接通信できる構成になっていた問題を修正。`permissions.<name>.network.enabled = true` はプロキシを起動しないため、許可ドメイン指定時は config.toml に `features.network_proxy = true`、requirements.toml に `[experimental_network]`（`managed_allowed_domains_only = true`）を出力する。`[experimental_network]` は experimental 扱いでネイティブ Windows の対応が限定的なため、受入テストでの確認を前提とする旨を生成 README と docs に明記。

## 2026-08-04

### Added
- generator: 生成される `settings.json` / `managed-settings.json` の `sandbox.network` に `strictAllowlist: true` を追加（docs/11 11.4/11.5 の例と一致）。許可リスト外ホストの扱いを「確認」から「拒否」へ固定する（v2.1.219 未満のクライアントでは無視され、従来の確認フローに落ちる）。

### Changed
- docs: 2026-06-24 以降の製品アップデートを一次資料で確認し反映。
  - Codex: `web_search` が `indexed`（検索インデックス承認URLに限る外部取得）を加えた4値に。業務既定は引き続き `cached` / `disabled` を推奨（docs/10・12・付録C）。managed requirements 取得失敗時の公式記載が fail-open から **fail-closed 方向へ更新**されたことを反映（実挙動の受入テスト必須は維持。docs/10 10.3.2）。filesystem の `:root` トークンが現行 config-reference から消失している点に導入時確認の注記を追加（docs/10 10.4・付録C）。`[mcp_servers]` identity allowlist（空テーブルで全MCP無効）等の新 managed キーを付録Cへ記録。公式ドキュメントの `learn.chatgpt.com` への恒久移転（308リダイレクト）を確認し出典URLを更新（付録C・docs/20）。
  - Claude Code（v2.1.221 時点）: `sandbox.credentials` のスキーマ公開（`deny`/`mask`・`injectHosts`）、`sandbox.filesystem.disabled`（避ける設定として 11.8 へ追加）、`sandbox.network.strictAllowlist`・`tlsTerminate` を反映（docs/11・付録C）。Issue #44642（`disableBypassPermissionsMode` 無効）が **closed（not planned）のまま修正されない**ことを明記し、受入テスト＋外部境界での代替を強調（docs/00・11・15・付録C）。`--no-session-persistence` は print mode 限定で、全モードは `CLAUDE_CODE_SKIP_PROMPT_HISTORY` を使う点を反映（docs/08・11・付録C）。
- 付録C の基準確認日を 2026-06-24 から 2026-08-04 に更新。
- docs/11: 11.4 に `sandbox.failIfUnavailable` 未設定時は fail-open である旨の注記を追加し、11.8 のアンチパターン記述との内部矛盾を解消。docs/10: 10.5 に requirements.toml のネットワーク許可リスト形式（generator の出力形式）を明記。

### Fixed
- docs/07・generator: パッケージレジストリへの公開（`npm publish`、`gradle publish`、`twine upload` 等）を 07.3 の原則拒否候補に明記し、generator の gradle スタックから `publish` の ask 昇格を除去（全スタックで publish/upload を allow/ask に置かないことをテストで固定）。
- generator: docs（正典）との整合監査で見つかった生成値のずれを修正:
  - `requirements.toml` の org-workspace に `:workspace_roots` の read 保護（`.devcontainer` / `.codex` / `.git`）を追加（docs/10 10.5 の例と一致）。
  - `settings.json` の ask に `WebSearch` を追加（docs/11 11.4 の例と一致。managed 側は従来どおり deny のみ）。
  - `managed-settings.json` の ask に `Bash(git commit *)` を追加（docs/11 11.5 の例と一致）。
  - L1 の Codex `config.toml` から `extends = ":workspace"` 前提のヘッダーコメントを除去（L1 は `:read-only` のため実体と矛盾していた）。
- generator: plan 質問のヘルプ文の誤記を修正。`requirements.toml` は team なら全レベルで生成され、team かつ L3+ 限定なのは `managed-settings.json` のみ。

## 2026-07-07

### Added
- generator: 選択・検出したスタックに応じてパッケージレジストリドメイン（npm → `registry.npmjs.org`、pip → `pypi.org` / `files.pythonhosted.org`、maven / gradle → `repo.maven.apache.org`（gradle は `plugins.gradle.org` も）、go → `proxy.golang.org` / `sum.golang.org`、dotnet → `api.nuget.org`）を許可ドメインの既定として対話時に提案。既定のままでも依存取得が遮断されない構成を最小許可で実現する。提案は対話フロー限定で、`--profile` 再生成は従来どおり profile の明示値のみを使用（再現性・監査記録は不変）。

### Changed
- generator: 生成される Claude Code 設定（`settings.json` / `managed-settings.json`）の allow に読み取り専用の `Bash(git log *)` を追加（docs/07 7.1 の自動許可候補との整合）。
- docs/11 の 11.4 / 11.5 設定例に `Bash(git log *)` を追加し、docs/10・docs/11 にレジストリドメイン既定提案の注記を追記（正典＝生成設定の一致を維持）。

## 2026-06-30

### Added
- 「指示・拡張レイヤー」を制御面として整理（02.7 新設）。プロジェクト指示・パススコープルール・スキル・サブエージェント・出力スタイルを、隔離境界ではなく「リポジトリ由来としてレビュー＋権限・サンドボックスで統制」する枠組みとして記述。
- Claude Code 固有の統制を 11.9 に新設。サブエージェント・出力スタイル・スキル・ルールについて、管理キーの有無と推奨統制（ファイルレビュー＋権限・サンドボックス＋外側境界）を表で整理。
- 13.2 と付録C に Claude Code の管理キーを追記: `disableBundledSkills`（`disableWorkflows` 併記）・`disableAgentView`・`disableSideloadFlags`・`disabledMcpjsonServers`・`disableAllHooks`。`outputStyle` は選択のみで無効化キーは未提供、`.claude/rules` の制御キーも未提供である旨を明記。
- 導入前チェックリスト（16.6）に、指示・拡張ファイルのコードレビュー化・安全指示の上書き確認・サブエージェント経由ツール実行の境界確認の3項目を追加。

## 2026-06-24

### Added
- 資格情報ガードの新手段を docs 化: `sandbox.filesystem.allowRead`（プロジェクト設定限定の堅牢パターン）、`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`、`sandbox.credentials`。
- generator: `managed-settings.json` に `requiredMinimumVersion` を追加（profile の `claude_min_version` 指定時のみ出力）。
- `deniedMcpServers`・モデル許可リスト（`availableModels` / `enforceAvailableModels`）の記載。
- Codex の追加サーフェス（Noise 暗号化リレー・マルチエージェント委譲の admin 制御・rollout トークン予算）を 10.7 に追記。
- 受入テスト（docs/15）に `requiredMinimumVersion` 未満拒否・堅牢 denyRead パターンの2観点を追加。

### Changed
- 付録C の基準確認日を 2026-06-20 から 2026-06-24 に更新。
- Issue #43713 を「バイパス報告」から「シェル展開で過剰にプロンプトが出る別件（open）」へ再分類（#29016 のバイパス警告は維持）。
- Codex `web_search` は `disabled` / `cached` / `live` の3値のまま（changelog で告知された indexed 機能は config トークン非公開のため値追加せず）。

## 2026-06-20

### Added
- セキュリティ・運用ガイド初版（`docs/`: レッドライン、レベル L0〜L4 × プラン × 製品、Codex / Claude Code 個別方針、MCP・Plugins・Hooks、Git/CI・CD、受入テスト、付録 A〜C ほか）。
- 生成ツール初版（`generator/`: `agentsec/` パッケージ、`templates/`、`generate.py` CLI、自己点検 `selfcheck.py`）。generator UX フェーズ1/2・docs 整合監査を含む。
