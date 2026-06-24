# 設計仕様: CHANGELOG の導入と運用

- 作成日: 2026-06-24
- 種別: 新規成果物（`CHANGELOG.md`）＋運用プロセス
- 関連: `docs/README.md`（版・発行日）、`docs/appendix-c-volatile-values.md`（基準確認日）、`AGENTS.md`、`CLAUDE.md`

## 1. 目的とスコープ

本リポジトリの変更履歴を人間が追えるよう、ルートに `CHANGELOG.md` を新設し、継続運用する。**リポジトリ全体（docs ガイド＋generator）を一本の CHANGELOG** で扱い、セクション粒度では Keep a Changelog の標準カテゴリで区別する。

### 非スコープ（YAGNI）

- git タグの自動付与、CI 連携、コミットからの完全自動生成スクリプトは作らない。
- generator のコード変更・テストは伴わない（純粋にドキュメント＋運用ルールの追加）。
- 過去の全マイルストーンの精密な再構成はしない（後述の最小遡及に留める）。

## 2. 形式と構造

- 場所: リポジトリルート `CHANGELOG.md`。
- 規約: [Keep a Changelog](https://keepachangelog.com/) 準拠。
- リリース見出し: **`## [X.Y.Z] - YYYY-MM-DD`**（semver ＋ 日付併記）。
- 記述言語: **日本語**（設定キー名・技術用語・製品名は原文のまま）。docs と同じ読者層。
- カテゴリ見出し: Keep a Changelog 標準の英語ラベルを使用 — `### Added` / `### Changed` / `### Deprecated` / `### Removed` / `### Fixed` / `### Security`。各カテゴリの本文は日本語の箇条書き。
- 先頭に常時 `## [Unreleased]` 節を置く（未リリースの蓄積先）。
- ファイル冒頭にヘッダ（本 CHANGELOG の規約・採番ルールへの簡潔な案内）を置く。

## 3. semver 採番ルール（本リポジトリ向けに固定）

docs ガイドと generator の混在を踏まえ、各増分の意味を次のとおり固定する。判断は「正典値・不変条件・generator 生成物への影響度」を基準にする。

| 区分 | 対象 |
|---|---|
| **MAJOR**（X） | レッドライン/不変条件・正典値の**破壊的変更**、章構成の大改訂、generator 生成物の後方非互換変更 |
| **MINOR**（Y） | 新しい推奨・設定キーの追加、generator の機能追加、新章の追加 |
| **PATCH**（Z） | 誤記修正、確認日のみの更新、文体・リンク整理など正典値に影響しない小修正 |

初期バージョンは `1.0.0`（初版）から始める（`0.x` は使わない。ガイドは既に実運用前提のため）。

## 4. 初期内容（最小遡及）

作成時点の `CHANGELOG.md` は次の3節構成とする。

- `## [Unreleased]` — 空（見出しのみ）。
- `## [1.1.0] - 2026-06-24` — 2026-06 製品アップデート反映（本セッションでマージ済みの内容）。
  - `### Added`: 資格情報ガード新手段の docs 化（`sandbox.filesystem.allowRead`・`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`・`sandbox.credentials`）／generator に `requiredMinimumVersion` を追加（profile 指定時のみ生成）／`deniedMcpServers`・モデル許可リスト（`availableModels`/`enforceAvailableModels`）の記載／Codex 追加サーフェス（Noise リレー・委譲 admin 制御・rollout トークン予算）／受入テスト2観点。
  - `### Changed`: 付録C 基準確認日を 2026-06-24 に更新／Issue #43713 を「バイパス」から「シェル展開で過剰プロンプトが出る別件（open）」へ再分類（#29016 のバイパス警告は維持）／Codex `web_search` は3値のまま（indexed は config トークン非存在を明記）。
- `## [1.0.0] - 2026-06-20` — セキュリティ・運用ガイド初版。
  - docs（L0〜L4 × プラン × 製品）、generator 初期版、付録C 等を含む 2026-06-20 時点の一式。間の generator UX フェーズ1/2・docs整合監査は 1.0.0 に内包する（最小遡及）。

各エントリ本文は簡潔な1行を基本とし、必要に応じて関連 spec/plan やコミットを参照しない（CHANGELOG は読者向けの要約に徹する）。

## 5. 運用フロー（ユーザー起動・差分ベース）

CHANGELOG の更新は**ユーザーの明示指示で行う**（作業ブランチの有無に依存しない）。自動的・常時の更新はしない。

1. ユーザーが「**changelog を更新して**」と指示する。
2. エージェントは「前回 CHANGELOG を更新した時点からの差分」を集約する。基準点は **`CHANGELOG.md` を最後に変更したコミット**とし、次で求める:
   - `git log -1 --format=%H -- CHANGELOG.md` で直近の CHANGELOG 変更コミットを取得。
   - そのコミット（exclusive）から `HEAD` までの `git log` / `git diff` を読み、変更を把握する。
   - Conventional Commits の type（`feat`/`fix`/`docs` 等）を Keep a Changelog カテゴリへの分類のヒントに使う（`feat`→Added/Changed、`fix`→Fixed、セキュリティ関連→Security 等）。
3. 把握した変更を **`## [Unreleased]` 節**へカテゴリ分けして追記する（日本語・要約）。リリース番号はまだ付けない。
4. **リリース確定は別の明示指示**（例: 「1.2.0 で切って」「リリースして」）で行う。そのとき:
   - `[Unreleased]` の内容を `## [X.Y.Z] - <当日日付>` へ移し、§3 のルールで採番する。
   - `[Unreleased]` は空の見出しとして残す。
   - `docs/README.md` の「**版**」を当該 semver に更新する（例: `版: 1.2.0（YYYY-MM-DD）`。人間向けに「初版」等のラベルを併記してよい）。
5. 上記手順を **`AGENTS.md`（プロジェクト指示）に明記**し、エージェントが一貫して従えるようにする。`CLAUDE.md` は `AGENTS.md` へのシンボリックリンク（内容同一）のため、`AGENTS.md` への記載で `CLAUDE.md` も同時に満たされる。編集対象は `AGENTS.md` のみとする。

## 6. 既存メタとの整合

- `docs/README.md` の「版／発行日」は、リリース確定時に CHANGELOG の最新 semver・日付と一致させる（§5.4）。
- `docs/appendix-c-volatile-values.md` の「基準確認日」は従来どおり docs 内で維持する。確認日を更新した際は、CHANGELOG の `### Changed` に1行記録して相互にたどれるようにする。
- CHANGELOG と docs/README/付録C の3者が乖離しないよう、リリース確定手順（§5.4）に README 版更新を必ず含める。

## 7. 受け入れ条件

- ルート `CHANGELOG.md` が存在し、§2 の形式（Keep a Changelog・semver＋日付・日本語・標準カテゴリ・先頭 [Unreleased]）に従う。
- §4 の初期内容（[Unreleased]＋1.1.0＋1.0.0）が記載されている。
- `AGENTS.md` に §5 の運用フロー（ユーザー起動・差分基準＝CHANGELOG 最終変更コミット・[Unreleased] 追記・リリース確定時の README 版更新）が明記されている。
- `docs/README.md` の版表記が CHANGELOG 最新版（1.1.0 / 2026-06-24）と整合する。
- generator のテストは不変で全 PASS（本変更はコード非変更）。
