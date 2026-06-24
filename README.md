# コーディングエージェント業務利用 セキュリティ・運用キット

コーディングエージェント（Codex / Claude Code 等）を業務・プロジェクトで安全に導入するための、**ガイド**と、それを実際の設定へ落とし込む**生成ツール**をまとめたリポジトリです。

- **`docs/`** — 業務利用レベル（L0〜L4）× 契約プラン（個人系 / チーム・ビジネス系）× 製品ごとに、与える権限を段階的に設計するためのセキュリティ・運用ガイド。まず[`docs/00-red-lines.md`（レッドライン）](docs/00-red-lines.md)と[`docs/README.md`](docs/README.md)を参照してください。
- **`generator/`** — ガイドの内容を、すぐ使える設定・コンテナ定義・受入テスト雛形・案件ポリシーシートへ変換する対話型生成スクリプト（Python 標準ライブラリのみ）。

## ディレクトリ構成

```
.
├── docs/         セキュリティ・運用ガイド（製品非依存層 + 製品固有層）
└── generator/    設定ジェネレータ（agentsec パッケージ + テンプレート + CLI）
```

## クイックスタート（ジェネレータ）

前提: Python 3.11 以上（標準ライブラリのみ。追加インストール不要）。Windows / Linux / macOS で同じスクリプトが動きます。

```bash
cd generator

# 対話的に生成（製品・レベル・プラン・スタック等を質問形式で入力）
python3 generate.py --output ./generated

# プロファイルから非対話で再生成（案件の再現・チーム展開・CI 向け）
python3 generate.py --profile profiles/examples/L2-team-both.json --output ./generated

# 生成物の静的セルフチェック（CI に組み込み可）
python3 generated/acceptance/selfcheck.py ./generated
```

## 生成される成果物

| 成果物 | 内容 |
|---|---|
| `claude-code/.claude/settings.json` | Claude Code のプロジェクト設定（補助設定） |
| `claude-code/managed-settings.json` | 組織強制設定（**チーム系 かつ L3+** のときのみ） |
| `codex/.codex/config.toml` / `codex/requirements.toml` | Codex の開発者設定 / 管理要件（requirements はチーム系のみ） |
| `Dockerfile` / `docker-compose.yml` / `.devcontainer/` / `.dockerignore` | 非root・最小権限のコンテナ定義（コンテナ有効時） |
| `acceptance/checklist.md` | 受入テストのチェックリスト（[`docs/15`](docs/15-acceptance-tests.md) 準拠） |
| `acceptance/selfcheck.py` | レッドラインの静的検査スクリプト（生成物に同梱・standalone） |
| `POLICY-SHEET.md` | 案件別ポリシー記入シート（[付録A](docs/appendix-a-policy-template.md) 準拠、逸脱事項を明記） |
| `README.md` | 適用手順と、遮断の根拠・逸脱一覧 |
| `generation-profile.json` | 再現用プロファイル + 各ファイルの SHA-256・逸脱レジスタ（監査記録） |

## 設計の要点

- **リスク受容を一級市民として扱う**: ガイドの MUST（[`docs/00` レッドライン](docs/00-red-lines.md)）と SHOULD（推奨）を区別します。
  - **レッドライン違反は既定で生成拒否。** 続行には `--allow-redline-override` と `--approver <名前>` が必須で、逸脱理由・承認者・日付が記録されます。
  - **SHOULD 逸脱は記録した上で続行。** 逸脱は `generation-profile.json` / `POLICY-SHEET.md` / `README.md` の3か所に残り、追跡可能です。
- **「設定した」ではなく「実際に拒否される」**: 同梱の `selfcheck.py` は**静的確認**に過ぎません（記録済みでもレッドライン違反は常に FAIL）。実拒否は必ず[`docs/15` 受入テスト](docs/15-acceptance-tests.md)で実環境・実バージョンに対して検証してください。

## テスト

```bash
cd generator
python3 -m unittest discover -s tests
```

## 変更履歴

変更履歴は[`CHANGELOG.md`](CHANGELOG.md)を参照（日付見出しの逆年代ログ。更新手順は[`AGENTS.md`](AGENTS.md)「CHANGELOG の運用」）。

## 設計ドキュメント

- 実装計画: [`docs/superpowers/plans/2026-06-21-agent-config-generator.md`](docs/superpowers/plans/2026-06-21-agent-config-generator.md)
- 設計仕様（個別）: [`docs/superpowers/specs/`](docs/superpowers/specs/)
