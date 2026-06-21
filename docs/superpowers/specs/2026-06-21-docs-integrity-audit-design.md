# docs 整合監査パス 設計（generator）

**日付:** 2026-06-21
**対象:** `generator/`（`agentsec/selfcheck.py`・`agentsec/build_codex.py`・`templates/policy/policy-sheet.md.tmpl`・`agentsec/readme.py`）

## 背景

フェーズ1・2（UX 改善）完了後の積み残しとして、正典 docs（`docs/00-red-lines.md`・`docs/10-codex.md`・`docs/11-claude-code.md`）と生成コードの不整合を監査した。あわせて、配置スコープ深掘り（フェーズ3候補）は「権限はメイン/サブプロジェクト一律・不都合は手動調整で運用」というユーザー判断により**新規実装不要（YAGNI）**と結論し、唯一の積み残し（モノレポ/複数マウント時の配置先ガイド）のみ本パスで回収する。

## 監査結果と判定（実物確認済み）

| # | 項目 | 実態 | 判定 |
|---|---|---|---|
| F1 | policy-sheet 節番号飛び（1,2,3,5,12） | `policy-sheet.md.tmpl` が 4,6〜11 を欠番 | 化粧。連番（1〜5）に振り直す |
| F2 | Codex network 三重設定 | `build_config`/`build_requirements` で `network` を作成→代入→ドメイン有時に作り直し | 軽微・無害。1回で組む整理（挙動不変） |
| F3 | L4 web_search が config(`disabled`)/requirements(`cached`)で不整合 | docs 10.3.2/10.5 に「`disabled` は常に許可」と明記。矛盾ではない | 非問題。コメント1行で意図明記のみ |
| F4 | selfcheck が Codex 設定を未検査 | selfcheck は claude settings/managed/compose/profile のみ検査 | 実ギャップ。Codex 検査を追加 |
| F5 | 生成漏れ未検出 | selfcheck は存在ファイルのみ走査。team+L3+ で managed 欠落等を検出不能 | 実ギャップ。完全性検査を追加 |

## 制約（厳守）

- Python 3.11+ / 標準ライブラリのみ。TOML 読み取りは `tomllib`（標準・読取専用）。書き込みは追加しない。
- `agentsec/selfcheck.py` は **standalone を維持**（`from agentsec import ...` を入れない。生成物へ verbatim コピーされ単体実行されるため）。
- ドメイン不変条件：生成値と docs（00/10）を一致させる。selfcheck は**静的確認に過ぎない**（実拒否は受入テストで確認する旨の注記を維持）。
- 改行 LF、パスは `pathlib`、I/O は `encoding="utf-8"`。テストは標準 `unittest`。TDD。

## 設計

### A. selfcheck.py の構造

- `import tomllib` を追加。
- 新規純関数：`_check_codex_config(path, msgs)`・`_check_codex_requirements(path, msgs)`・`_check_completeness(root, msgs)`。
- `check_dir(output_dir)` から上記を呼ぶ：
  - `codex/.codex/config.toml` を `rglob` し `_check_codex_config`。
  - `codex/requirements.toml` を `rglob` し `_check_codex_requirements`。
  - `generation-profile.json` が存在する場合に `_check_completeness`（無ければスキップ）。
- 既存の PASS/WARN=0・FAIL=2 の戻り規約は維持。

### B. F4：Codex レッドライン静的検査

**`_check_codex_config`**（`config.toml` を tomllib で解析）
- R3：`default_permissions == ":danger-full-access"`、または任意の `permissions.<name>.extends == ":danger-full-access"` → `FAIL ... (00 R3)`。
- 10.8：`approval_policy == "never"` → `FAIL ... (10.8)`。
- R2（.env read deny）：**workspace-write プロファイルが存在するときのみ**チェック。`permissions.<name>.filesystem.":workspace_roots"` に `.env` を含むキーで値 `"deny"` が無ければ `FAIL ... (00 R2)`。
  - L1 の `:read-only` 構成は `permissions` セクションを持たないため**スキップ**。L1 は docs 10.3.1 のとおり外部境界（コンテナ/VM/ネットワーク）で .env を遮断する前提（この設計判断を本 spec に明記）。

**`_check_codex_requirements`**（`requirements.toml`、team プランのみ生成）
- R3：`allowed_permission_profiles` が `":danger-full-access"` を `true` で含まないこと。
- R2：`permissions.filesystem.deny_read` が `.env`（`**/.env` 等いずれか）と資格情報（`~/.ssh` 等いずれか）を含むこと。
- R4：`rules.prefix_rules` に `git push` と `sudo` を `forbidden` とするルールがあること。
- 10.3.2：`allowed_web_search_modes` に `"live"` を含まないこと。

### C. F5：生成漏れ検出（`_check_completeness`）

`generation-profile.json` の `data["profile"]`（`products`・`level`・`plan`・`use_container`）から**期待ファイル集合を独立に導出**し、`root` 直下に存在しなければ `FAIL ... 生成漏れ`。

| 条件 | 期待ファイル |
|---|---|
| `"claude" in products` | `claude-code/.claude/settings.json` |
| `"claude" in products` かつ `plan=="team"` かつ `level in ("L3","L4")` | `claude-code/managed-settings.json` |
| `"codex" in products` | `codex/.codex/config.toml` |
| `"codex" in products` かつ `plan=="team"` | `codex/requirements.toml` |
| `use_container` が真 | `Dockerfile` / `docker-compose.yml` / `.devcontainer/devcontainer.json` / `.dockerignore` |
| 常に | `acceptance/checklist.md` / `acceptance/selfcheck.py` / `POLICY-SHEET.md` / `README.md` / `generation-profile.json` |

- ゲーティング規則を selfcheck 側へ独立再記述＝`orchestrate` とのドリフト検出。
- `generation-profile.json` が無い場合は完全性検査を**スキップ**（手配置成果物にも selfcheck を流せるよう、現行挙動を壊さない）。

### D. 機械的修正

- **F2**：`build_config`・`build_requirements` の network を「`network = {"enabled": bool(allowed_domains)}` を作り、`allowed_domains` 真のとき `network["domains"] = {d: "allow" for d in allowed_domains}` を足して**1回だけ代入**」へ整理。出力 TOML は現行と同一。
- **F1**：`policy-sheet.md.tmpl` の見出し番号を `1.〜5.` の連番へ（分類/実行環境/ファイル・コマンド/ネットワーク/逸脱事項 の現行5節・現行順を維持しつつ連番化）。
- **F3**：`build_requirements` の `allowed_web_search_modes` 行付近に「`disabled` は常に許可ゆえ L4 の config=`disabled` と矛盾しない」コメントを追加。
- **placement_guide**：`readme.placement_guide` に、モノレポ/複数マウント時は**単一の助言設定をワークスペース/コンテナ共通の場所（例：コンテナ home の `~/.claude/`・`~/.codex/`）に1つ配置すれば全サブプロジェクト/全マウントに効く**旨を1〜2行追記。

### E. テスト

- `tests/test_selfcheck.py`：
  - F4 config：danger-full-access（default/extends 両方）で FAIL、approval_policy=never で FAIL、L2 正常構成で PASS、L1 read-only で .env チェックがスキップされ PASS。
  - F4 requirements：danger-full-access 許可で FAIL、deny_read に .env/資格情報欠落で FAIL、prefix_rules に git push/sudo 欠落で FAIL、live 含有で FAIL、正常 requirements で PASS。
  - F5：team+L3+ で managed 欠落 → FAIL、codex+team で requirements 欠落 → FAIL、use_container で Dockerfile 欠落 → FAIL、`generation-profile.json` 無し → 完全性検査スキップ、完全な出力 → PASS。
- `tests/test_build_codex.py`：F2 リファクタ後も network セクションの出力値（enabled・domains）が現行と一致（挙動不変回帰）。
- `tests/test_readme.py`：placement_guide の追記文言を検証。
- 統合スモーク：`python3 generate.py --profile profiles/examples/L2-team-both.json --output /tmp/gen-smoke` → `python3 /tmp/gen-smoke/acceptance/selfcheck.py /tmp/gen-smoke` が exit 0。

## 非目標（YAGNI）

- 配置スコープのサブプロジェクト別分解（案2/案3）。権限一律のため不要。
- L1 Codex の .env read 遮断を config 内で行う変更。外部境界で担保する docs 10.3.1 の設計に従い、本パスでは扱わない（必要なら別途課題化）。
- selfcheck による Claude 側 web_search/その他 SHOULD 群の網羅。本パスはレッドライン（MUST）＋生成完全性に限定する。
