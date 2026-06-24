# AGENTS.md

## このリポジトリの構成

- `docs/` — コーディングエージェント業務利用のセキュリティ・運用ガイド（レベル L0〜L4 × プラン × 製品）。値の**正典（source of truth）**。
- `generator/` — ガイドを実設定へ変換する対話型生成ツール（`agentsec/` パッケージ + `templates/` + `generate.py` CLI）。
- `docs/superpowers/` — 設計仕様（`specs/`）と実装計画（`plans/`）。

## 開発の制約（厳守）

- **Python 3.11 以上、標準ライブラリのみ。** サードパーティ依存を追加しない（`pip install` なしで動くこと）。
- **TOML 書き込みは自前の `agentsec/render_toml.py` を使う。** `tomli_w` 等を追加しない（`tomllib` は読み取り専用）。
- **`agentsec/selfcheck.py` は standalone を保つ。** `from agentsec import ...` を入れない。生成物へ verbatim コピーされ単体で実行されるため。
- **テストは標準 `unittest`。** 実行: `cd generator && python3 -m unittest discover -s tests`
- 改行は **LF**。パス操作は `pathlib`、ファイル I/O は `encoding="utf-8"`。
- `agentsec/` はロジックのみ。対話 I/O は `generate.py` に閉じ込める（関数は引数で値を受け取りテスト可能にする）。
- 新機能・変更時は **TDD**（失敗するテスト → 実装 → 通過）。

## ドメイン上の不変条件

- ガイドの値（`docs/00-red-lines.md`・`docs/10-codex.md`・`docs/11-claude-code.md`）と生成設定を**一致**させる。設定を変えるときは対応する docs を確認する。
- **レッドライン（MUST）は既定で生成拒否。** 続行は `--allow-redline-override` + `--approver` のみ。SHOULD 逸脱は記録して続行。逸脱は `generation-profile.json` / `POLICY-SHEET.md` / `README.md` の3か所に残す。
- `managed-settings.json` を生成するのは **チーム系 かつ L3+** のときのみ。
- `selfcheck.py` は**静的確認**に過ぎない（記録済みでもレッドライン違反は常に FAIL）。実拒否は `docs/15-acceptance-tests.md` の受入テストで検証する旨を成果物に明記し続ける。

## Git / コミット

- コミットメッセージは英語・Conventional Commits（`feat:` `fix:` `docs:` `chore:` `test:` 等）。subject は命令形・小文字始まり・末尾ピリオドなし、おおむね50文字以内。
- デフォルトブランチ上では作業ブランチを切ってから着手する。コミット/プッシュはユーザーの依頼時のみ。
- Claude を共著者に含める場合は次の形式（モデル名は含めない）:

  ```
  Co-authored-by: Claude <noreply@anthropic.com>
  ```

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

## 変更後の検証

```bash
cd generator && python3 -m unittest discover -s tests
# 生成→セルフチェックのスモーク
python3 generate.py --profile profiles/examples/L2-team-both.json --output /tmp/gen-smoke
python3 /tmp/gen-smoke/acceptance/selfcheck.py /tmp/gen-smoke   # exit 0 を確認
# 対話生成で対象プロジェクトを自動検出（カレント以外を見る場合）
python3 generate.py --target-dir /path/to/project --output /tmp/gen-detect
```
