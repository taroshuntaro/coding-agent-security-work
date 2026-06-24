# 設計仕様: 2026-06 製品アップデート反映

- 作成日: 2026-06-24
- 種別: docs 値更新 ＋ generator 最小反映
- 関連: [付録C 揮発値一覧](../../appendix-c-volatile-values.md)、[17 定期レビュー](../../17-periodic-review.md)

## 1. 目的とスコープ

付録C の基準確認日 **2026-06-20** 以降に確認された Claude Code / Codex の更新のうち、本ガイドの正典値・推奨手法に影響するものを反映する。1つの spec に全項目を集約し、実装計画（plan）で 3 フェーズに分割する。

- フェーズ1: 高影響（docs 値の再検証＋更新）
- フェーズ2: 中影響（新キーの docs 記載 ＋ generator 最小反映）
- フェーズ3: 補足（既知ギャップの裏取り・軽微な追記）

### 維持すべき不変条件

- docs の値（`00`/`10`/`11` 等）＝ generator 生成設定を**一致**させる。
- 付録C の検証状態（✅/⚠️）と**基準確認日を 2026-06-24 へ更新**する。
- `selfcheck.py` は static 確認のみ・standalone を維持。実拒否は `docs/15` 受入テストで検証する建付けを崩さない。
- generator 変更は TDD。`python3 -m unittest discover -s tests` 全通過 ＋ 生成→selfcheck exit 0 のスモークを満たす。
- レッドライン（MUST）の生成拒否ロジックには手を入れない。

### 出典の信頼区分（本 spec の前提）

- **一次資料で確認済み**（公式 docs / 公式 CHANGELOG / GitHub Issue）: ✅ 扱いで反映。
- **二次資料のみ**（ブログ・更新集約サイト）: 反映時に必ず一次資料で再確認。確認できない限り、**既存のセキュリティ警告のトーンを弱める方向へは変更しない**（後述 R1）。

## 2. フェーズ1（高影響・docs 値の更新）

### 2.1 資格情報ガードの新手段（最重要）

本ガイドの中核警告は「Bash サンドボックスは既定で `~/.aws`・`~/.ssh` を読めるので `denyRead` 必須」（`08.1` WARNING / `11.1` WARNING / `11.4` / `C.2`）。新しい選択肢を反映する。

- **`sandbox.filesystem.allowRead`**（公式 sandboxing docs で確認済み・✅）— `denyRead` 領域内の特定パスを再許可。
  - プロジェクト `settings.json` に限り、堅牢パターン **`denyRead: ["~/"]＋allowRead: ["."]`**（ホーム全体を遮断しプロジェクトのみ開放）を追加例として記載する。
  - **重要な制約**: `"."` はプロジェクト設定でのみプロジェクトルートに解決される。`~/.claude/settings.json` や `managed-settings.json` に置くと `~/.claude` に解決され意図がずれる。**この堅牢パターンはプロジェクト `settings.json` 限定**であり、グローバル/管理設定では従来どおり明示的な資格情報ディレクトリ列挙（`~/.ssh`・`~/.aws`・`~/.kube`）を使う旨を明記する。
- **`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`**（公式 env-vars docs で確認済み・✅）— サンドボックス内サブプロセスの環境変数から Anthropic・クラウド資格情報を除去。`08`（シークレット）に「ファイル read deny だけでは環境変数経由の資格情報は残る」観点で追記し、`11` から参照する。
- **`sandbox.credentials`**（CHANGELOG v2.1.187 報告・**一次の settings リファレンス未掲載**）— 資格情報ファイル＋シークレット環境変数の読み取りを一括ブロックする設定。**⚠️ として C.2 に追加**し「導入時に対象バージョンの公式 settings リファレンスで正式キー名・実効性を確認」と注記。本文では断定しない。

対象ファイル: `08-secrets.md`、`11-claude-code.md`（11.1/11.4/11.5）、`appendix-c-volatile-values.md`（C.2）。

### 2.2 `autoAllowBashIfSandboxed` バイパス記述の扱い（R1）

二次資料に「複合 Bash コマンド・env-var プレフィックス・`/dev/tcp` リダイレクト・パイプ `cd` による deny 降格などが修正された」との記載があるが、**一次資料（公式 CHANGELOG / Issue #29016・#43713）での closed 確認が前提**。

- 実装タスク: 該当 Issue と公式 CHANGELOG の状態を一次資料で確認する。
- closed が確認できた場合のみ、`11.4`/`C.2` に「vX で対処済み（確認日）」を**追記**する。既存の警告（受入テスト必須）は残す。
- 確認できない場合は、トーンを変えず「関連バイパスが対処された模様・要検証」と確認日付きで併記するに留める。
- **セキュリティ警告のトーンを二次情報だけで反転させない。**

対象ファイル: `11-claude-code.md`（11.4）、`appendix-c-volatile-values.md`（C.2）。

### 2.3 PreToolUse hook が deny を上書きするバグ修正（R1 適用）

「PreToolUse hook が `allow` を返すと deny 権限ルール（管理設定含む）をバイパスできた」問題の修正報告（二次資料）。2.2 と同じ方針で、一次資料で確認できた場合のみ `13`（MCP・Hooks の信頼境界）に確認日付きで記載する。

対象ファイル: `13-mcp-plugins-hooks.md`、`appendix-c-volatile-values.md`。

## 3. フェーズ2（中影響・新キー記載＋ generator 最小反映）

### 3.1 バージョン固定の管理設定（`requiredMinimumVersion` / `requiredMaximumVersion`）

公式 settings docs で確認済み（✅）。`17.2`／`10.5` が「管理設定が古いクライアントで無視されないか」「全台が対応バージョン以上か」を**運用で担保**していたギャップに対する製品側の強制手段。

- docs: `11.5`（managed-settings 例）・`17.2`・`appendix-c` C.2 に記載。
- generator（**R2**）: `requiredMinimumVersion` を **profile の任意フィールド**として受け取り、チーム系 L3+ の `managed-settings.json` 生成時に**指定があるときのみ**出力する。**具体バージョン番号の既定値は焼き込まない**（陳腐化回避）。未指定時は docs の誘導（手動設定）に委ねる。`requiredMaximumVersion` は docs のみ。
  - 実装位置: `agentsec/build_claude.py` の `build_managed_settings`。
  - selfcheck・unittest を拡充（指定時に出力されること／未指定時に出力されないこと）。

### 3.2 `deniedMcpServers`（allowlist 補完の denylist）

公式 settings docs で確認済み（✅）。`allowedMcpServers` を補完し denylist が優先。

- docs のみ: `11.5`・`13`・`appendix-c` C.2 に記載。generator 生成は見送り（YAGNI）。

### 3.3 モデル許可リスト強制（`availableModels` / `enforceAvailableModels`）

公式 settings docs で確認済み（✅）。データ越境・コスト統制の新サーフェス。

- docs のみ: `11.5`・`appendix-c` C.2 に新統制サーフェスとして記載。generator 生成は見送り。

### 3.4 Codex indexed web-search モード

Codex CLI 0.142.0（2026-06-22）で「ライブ検索は許すがページ直接取得をサーバー承認 URL に限定する」モードが追加（changelog で確認・**正式な列挙値トークン名は未確認**）。

- 実装タスク: 公式 config-reference で `web_search` / `allowed_web_search_modes` の正式な値トークンを確認（**R3**, ⚠️）。
- docs: `10.1`・`10.5`・`appendix-c` C.1 で `web_search` の選択肢・既定値・`allowed_web_search_modes` を更新。
- generator: `allowed_web_search_modes` の既知集合（値リスト）に追加するのみ。挙動ロジックは変えない。

## 4. フェーズ3（補足・軽微な追記）

- **Claude Code**:
  - `sandbox.allowAppleEvents`（macOS で Apple Events 既定ブロック・user/managed/CLI のみ有効、project 設定は無視）を `11.x` に例外として追記。`C.2` は既出のため確認日のみ更新。
  - 設定ファイルは全スコープ＋ managed ディレクトリで sandbox write 拒否（自己ポリシー改変不可）の保証を `11.x` に補強材料として追記。
  - ドメインフロンティング/TLS 非検査 ＋ `enableWeakerNetworkIsolation`・カスタムプロキシを `11.6`（ネットワーク区別）に「許可ドメインが広いと exfiltration 経路になり得る」観点で補強。
- **Codex**: `10.7`（追加サーフェス）に、リモート実行の Noise 暗号化リレー・rollout トークン予算・マルチエージェント委譲の admin 制御（disabled / explicit-request-only / proactive）を軽く追記。

## 5. 検証方針

- 各値は実装時に**対象公式ページで再確認**し、付録C の検証状態（✅/⚠️）と基準確認日（2026-06-24）を更新する。一次資料で確認できない項目は ⚠️ のまま据え置く。
- 受入テスト（`docs/15`）に、強制系の新コントロールの検証観点を追加する。
  - `requiredMinimumVersion` 未満のクライアントで起動が拒否されること。
  - 資格情報 read 遮断の堅牢パターン（プロジェクト設定の `denyRead:["~/"]＋allowRead:["."]`）で `~/.ssh` 等が読めないこと。
- generator 変更は TDD（失敗テスト→実装→通過）。`python3 -m unittest discover -s tests` 全通過、生成→`selfcheck.py` exit 0 のスモークを確認。
- docs↔generator の一致を `selfcheck` の既存整合チェックで担保。新キーを generator に出す場合は対応する整合テストを追加。

## 6. 非スコープ（YAGNI）

- `deniedMcpServers`・`availableModels`・`enforceAvailableModels` の generator 生成（docs 記載のみ）。
- `requiredMaximumVersion` の generator 生成。
- Codex `web_search` の挙動ロジック変更（値リスト追加に留める）。
- レッドライン生成拒否ロジック・`selfcheck` の standalone 構成への変更。
