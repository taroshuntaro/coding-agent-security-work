# Changelog

本リポジトリ（セキュリティ・運用ガイド `docs/` と生成ツール `generator/`）の変更履歴。

- [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) のカテゴリ（Added / Changed 等）を借りつつ、**日付見出し（`## YYYY-MM-DD`）の逆年代ログ**として運用する（リリース・版番号の概念は持たない）。
- 更新手順は `AGENTS.md`「CHANGELOG の運用」を参照。ユーザーの指示で更新する。

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
