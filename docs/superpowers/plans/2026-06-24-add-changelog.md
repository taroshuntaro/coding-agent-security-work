# CHANGELOG 導入 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ルートに `CHANGELOG.md` を新設し、その更新フローを `AGENTS.md` に明記する。

**Architecture:** ドキュメントのみの変更（generator のコード・テストは不変）。Keep a Changelog 準拠・semver＋日付・日本語の `CHANGELOG.md` を初期内容（[Unreleased]＋1.1.0＋1.0.0）で作成し、`docs/README.md` の版メタを 1.1.0 に整合させる。運用フロー（ユーザー起動・差分基準＝`CHANGELOG.md` 最終変更コミット）を `AGENTS.md` に追記する。

**Tech Stack:** Markdown のみ。検証は既存の generator `unittest`（不変で全 PASS であること）と git コマンドの目視。

## Global Constraints

- 記述言語は日本語（設定キー名・技術用語・製品名は原文のまま）。改行は LF、ファイル I/O は UTF-8。
- ルート `CHANGELOG.md`・[Keep a Changelog](https://keepachangelog.com/) 準拠・リリース見出しは `## [X.Y.Z] - YYYY-MM-DD`・カテゴリは `### Added / Changed / Deprecated / Removed / Fixed / Security`・先頭に常時 `## [Unreleased]`。
- 初期バージョンは `1.0.0` 始まり（`0.x` を使わない）。
- semver 採番ルール: MAJOR=レッドライン/不変条件・正典値の破壊的変更や章構成大改訂・generator 生成物の後方非互換、MINOR=新しい推奨・設定キー・generator 機能の追加、PATCH=誤記・確認日更新等の小修正。
- `CLAUDE.md` は `AGENTS.md` へのシンボリックリンク（内容同一）。編集対象は `AGENTS.md` のみ。
- generator のコード・テストは変更しない。
- 作業ブランチ: `docs/add-changelog`（作成済み）。コミットは英語・Conventional Commits、共著表記 `Co-authored-by: Claude <noreply@anthropic.com>`。
- spec: `docs/superpowers/specs/2026-06-24-changelog-design.md`。

---

### Task 1: CHANGELOG.md を作成し README の版メタを整合

**Files:**
- Create: `CHANGELOG.md`
- Modify: `docs/README.md`（冒頭の版／発行日／仕様確認基準日）

**Interfaces:**
- Produces: ルート `CHANGELOG.md`（[Unreleased]＋1.1.0＋1.0.0）。最新リリースは `1.1.0` / `2026-06-24`。

- [ ] **Step 1: `CHANGELOG.md` を作成**

リポジトリルートに `CHANGELOG.md` を次の内容で新規作成する（逐語）:

```markdown
# Changelog

本リポジトリ（セキュリティ・運用ガイド `docs/` と生成ツール `generator/`）の変更履歴。

- 形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠する。
- バージョンは [セマンティック バージョニング](https://semver.org/lang/ja/) を本リポジトリ向けに運用する（採番ルールは `AGENTS.md`「CHANGELOG の運用」を参照）。
- 更新手順は `AGENTS.md`「CHANGELOG の運用」を参照。ユーザーの指示で更新する。

## [Unreleased]

## [1.1.0] - 2026-06-24

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

## [1.0.0] - 2026-06-20

### Added
- セキュリティ・運用ガイド初版（`docs/`: レッドライン、レベル L0〜L4 × プラン × 製品、Codex / Claude Code 個別方針、MCP・Plugins・Hooks、Git/CI・CD、受入テスト、付録 A〜C ほか）。
- 生成ツール初版（`generator/`: `agentsec/` パッケージ、`templates/`、`generate.py` CLI、自己点検 `selfcheck.py`）。generator UX フェーズ1/2・docs 整合監査を含む。
```

- [ ] **Step 2: `docs/README.md` の版メタを更新**

`docs/README.md` 冒頭の次の3行:

```markdown
- **版**: 初版
- **発行日**: 2026-06-20
- **仕様確認基準日**: 2026-06-20
```

を次へ置換する（版を semver に、日付を 1.1.0 リリース・最新基準確認日へ整合。`仕様確認基準日` は付録C の基準確認日 2026-06-24 と一致させる）:

```markdown
- **版**: 1.1.0
- **発行日**: 2026-06-24
- **仕様確認基準日**: 2026-06-24
```

- [ ] **Step 3: 形式・整合の検証**

Run:
```bash
cd /Users/a160341/Documents/_work/coding-agent-security-work
head -1 CHANGELOG.md
grep -nE '^## \[(Unreleased|[0-9]+\.[0-9]+\.[0-9]+)\]' CHANGELOG.md
grep -n '仕様確認基準日' docs/README.md docs/appendix-c-volatile-values.md
cd generator && python3 -m unittest discover -s tests 2>&1 | grep -E '^(OK|FAILED|Ran )'
```
Expected:
- `# Changelog` が1行目。
- `## [Unreleased]` / `## [1.1.0] - 2026-06-24` / `## [1.0.0] - 2026-06-20` の3見出しが順に出る。
- README の `仕様確認基準日: 2026-06-24` が付録C の基準確認日と一致。
- generator テスト `OK`（142 件前後・不変）。

- [ ] **Step 4: コミット**

```bash
cd /Users/a160341/Documents/_work/coding-agent-security-work
git add CHANGELOG.md docs/README.md
git commit -m "docs: add CHANGELOG and align README version to 1.1.0" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

### Task 2: CHANGELOG 運用フローを AGENTS.md に明記

**Files:**
- Modify: `AGENTS.md`（新セクション「## CHANGELOG の運用」を追加）

**Interfaces:**
- Consumes: Task 1 で作成した `CHANGELOG.md`。

- [ ] **Step 1: `AGENTS.md` に運用セクションを追加**

`AGENTS.md` を Read し、「## Git / コミット」セクションの直後（「## 変更後の検証」の直前）に、次のセクションを挿入する（逐語）:

```markdown
## CHANGELOG の運用

ルート `CHANGELOG.md` は [Keep a Changelog](https://keepachangelog.com/) 準拠・semver＋日付（`## [X.Y.Z] - YYYY-MM-DD`）・日本語で管理する。**更新はユーザーの明示指示で行う**（自動・常時更新はしない）。

- **「changelog を更新して」と指示されたら**:
  1. 直近で CHANGELOG を変更したコミットを基準点にする: `git log -1 --format=%H -- CHANGELOG.md`。
  2. そのコミット（exclusive）から `HEAD` までの `git log` / `git diff` を読み、変更を把握する。Conventional Commits の type を分類のヒントにする（`feat`→Added/Changed、`fix`→Fixed、セキュリティ関連→Security 等）。
  3. 把握した変更を、日本語の要約として `## [Unreleased]` 節へカテゴリ（Added / Changed / Deprecated / Removed / Fixed / Security）別に追記する。リリース番号はまだ付けない。
- **「リリースして」「x.y.z で切って」等と指示されたら**:
  1. `[Unreleased]` の内容を `## [X.Y.Z] - <当日>` へ移す。`[Unreleased]` は空見出しで残す。
  2. 採番ルール: MAJOR＝レッドライン/不変条件・正典値の破壊的変更や章構成の大改訂・generator 生成物の後方非互換、MINOR＝新しい推奨・設定キー・generator 機能の追加、PATCH＝誤記・確認日更新等の小修正。
  3. `docs/README.md` の「版／発行日」を当該 semver・日付に一致させる。付録C の基準確認日を更新した場合は CHANGELOG の `### Changed` に1行記録する。
```

- [ ] **Step 2: 反映の検証**

Run:
```bash
cd /Users/a160341/Documents/_work/coding-agent-security-work
grep -n 'CHANGELOG の運用' AGENTS.md
grep -n 'CHANGELOG の運用' CLAUDE.md
```
Expected: 両方で当該見出しが1件ヒットする（`CLAUDE.md` はシンボリックリンクなので同内容を返す）。

- [ ] **Step 3: コミット**

```bash
cd /Users/a160341/Documents/_work/coding-agent-security-work
git add AGENTS.md
git commit -m "docs: document CHANGELOG maintenance workflow in AGENTS.md" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

## Self-Review（計画作成者による spec 突合）

- **spec §2 形式と構造** → Task 1 Step 1（Keep a Changelog・semver＋日付・日本語・標準カテゴリ・先頭 [Unreleased]・ヘッダ）。✅
- **spec §3 採番ルール** → Global Constraints ＋ Task 2 Step 1（AGENTS.md に明記）。✅
- **spec §4 初期内容（[Unreleased]＋1.1.0＋1.0.0）** → Task 1 Step 1。✅
- **spec §5 運用フロー（ユーザー起動・差分基準＝CHANGELOG 最終変更コミット・[Unreleased] 追記・リリース確定時の README 版更新）** → Task 2 Step 1。✅
- **spec §5.5 AGENTS.md に明記・CLAUDE.md はシンボリックリンク** → Task 2（編集は AGENTS.md のみ、Step 2 で CLAUDE.md 反映を確認）。✅
- **spec §6 既存メタ整合（README 版/発行日、付録C 基準確認日の相互参照）** → Task 1 Step 2（README 整合）＋ Task 2 Step 1（リリース手順に README 版更新・付録C 相互参照を含める）。✅
- **spec §7 受け入れ条件** → Task 1 Step 3 / Task 2 Step 2 の検証、generator テスト不変。✅
- **プレースホルダ走査**: `<当日>`・`<X.Y.Z>` は運用手順のテンプレート（意図的）。それ以外に TBD/TODO なし。✅
- **型整合**（ここでは見出し・ラベルの整合）: カテゴリラベル（Added/Changed/...）・見出し形式 `## [X.Y.Z] - YYYY-MM-DD`・基準点コマンド `git log -1 --format=%H -- CHANGELOG.md` が Constraints・CHANGELOG・AGENTS で一貫。✅
