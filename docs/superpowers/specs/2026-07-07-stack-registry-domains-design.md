# 設計仕様: スタック連動レジストリドメイン既定値 ＋ git log 自動許可

- 作成日: 2026-07-07
- 種別: generator 機能追加 ＋ docs 整合修正
- 関連: [07 共通の推奨コマンドポリシー](../../07-command-policy.md)、[11 Claude Codeの推奨方針](../../11-claude-code.md)

## 1. 目的とスコープ

本リポジトリの方針は「ガチガチの最大硬化」ではなく、**現実的な範囲で安全性と機能を両立し、不便なく作業できる環境の構築**である。この方針に照らし、生成設定に残っている2つの摩擦を解消する。

1. **スタック連動レジストリドメイン**: 現状、許可ドメインの既定は `github.com` / `objects.githubusercontent.com` のみ（`rules.DEFAULT_ALLOWED_DOMAINS`）。npm スタックを選んでも `registry.npmjs.org` が既定に入らないため、`npm install` を ask で承認してもサンドボックスのネットワーク遮断で失敗する。docs/11 の 11.4 例は `*.npmjs.org` を含み「実際のビルドツールに合わせて置き換える」と述べているが、generator がこれを体現していない。→ 選択・検出されたスタックに応じてレジストリドメインを**対話時の既定値として提案**する。
2. **`git log` 自動許可**: docs/07 の 7.1 は `git log` を自動許可候補に明記しているが、docs/11 の設定例と generator の allow には `git status` / `git diff` しかない。読み取り専用コマンドでありリスク増なしに確認回数を減らせるため、docs/11 例と generator の両方へ追加し正典整合を取る。

### 維持すべき不変条件

- docs の値 ＝ generator 生成設定の**一致**（AGENTS.md）。
- `--profile` 再生成は profile の明示値をそのまま使う（**再現性・監査記録は不変**）。動的既定は対話フローのみに影響する。
- レッドライン（MUST）の生成拒否ロジック、`selfcheck.py` の standalone 性には手を入れない。
- 標準ライブラリのみ・TDD・全テスト通過＋生成→selfcheck exit 0 のスモーク。

### スコープ外（検討の上で見送り）

- `autoAllowBashIfSandboxed: true` 化 — バイパス実例（Issue #29016）を理由に docs/11 が意図的に `false` としており、覆す一次情報がない。
- スタック別 typecheck / format コマンドの allow 追加 — スクリプト名がプロジェクトごとに異なり、既定として焼き込む価値が薄い（YAGNI）。
- ビルダー（`build_claude` / `build_codex`）内でのドメイン暗黙注入 — profile と出力が乖離し監査性を損なうため不採用。

## 2. 設計

### 2.1 スタック→レジストリドメインのデータ（`agentsec/stacks.py`）

`STACKS` 各エントリへ `"domains"` キーを追加し、`commands_for` と同形の純関数 `domains_for(stack_keys)`（union・sorted、未知キーは `ValueError`）を新設する。

| スタック | 追加ドメイン |
|---|---|
| npm | `registry.npmjs.org` |
| pip | `pypi.org`, `files.pythonhosted.org` |
| maven | `repo.maven.apache.org` |
| gradle | `repo.maven.apache.org`, `plugins.gradle.org` |
| go | `proxy.golang.org`, `sum.golang.org` |
| dotnet | `api.nuget.org` |

方針: 各パッケージマネージャの一次配布ドメインに限定した最小集合。ミラーや社内レジストリは利用者が対話時に編集して指定する（既定は提案であり強制注入ではない）。

### 2.2 動的既定の質問（`agentsec/questions.py`）

純関数 `allowed_domains_question(stack_keys)` を追加する。既存の `allowed_domains` 質問のコピーに対し、

- `default` = `rules.DEFAULT_ALLOWED_DOMAINS` ＋ `stacks.domains_for(stack_keys)`（重複排除・DEFAULT を先頭に維持）
- `detail` = 動的既定を反映した説明文（スタック由来分が含まれる旨を明示）

を設定して返す。`QUESTIONS` のデータ定義は変えない（profile スキーマ・キー順不変）。

### 2.3 対話フローの配線（`generate.py`）

`collect_interactive` で、スタック確定後に `allowed_domains` の質問だけ `questions.allowed_domains_question(a["stacks"])` へ差し替える。質問順（stacks → allowed_domains）は既存のまま。`--profile` 経路は一切変更しない。

### 2.4 `git log` 自動許可（`agentsec/build_claude.py` ＋ docs/11）

- `build_settings` / `build_managed_settings` の allow へ `Bash(git log *)` を追加（`git status` / `git diff *` の並び）。
- docs/11 の 11.4（settings.json 例）・11.5（managed-settings.json 例）の allow にも同じく追加。

### 2.5 docs 側の注記

- docs/11 の 11.4 例直後にある「生成ツール（`generator/`）は…」の段落付近へ、generator がスタックに応じてレジストリドメイン（例: npm → `registry.npmjs.org`）を対話時の既定として提案する旨を1行追記する。
- `generator/README.md` は既定ドメインに言及していないことを確認済みのため変更不要。

## 3. テスト（TDD）

- `test_stacks.py`: `domains_for` の union・sorted・未知キー `ValueError`・空リストで空。全スタックが `domains` キーを持つ整合テスト。
- `test_questions.py`: `allowed_domains_question(["npm"])` の default に `registry.npmjs.org` と `DEFAULT_ALLOWED_DOMAINS` が含まれる。空スタックなら既定のみ。元の `QUESTIONS` エントリが変異しないこと。
- `test_generate.py`: 対話フローでスタック選択後に空 Enter すると、profile の `allowed_domains` へスタック連動既定が入る。
- `test_build_claude.py`: settings / managed 双方の allow に `Bash(git log *)` が含まれる（既存アサーション更新）。
- 回帰: 既存全テスト通過 ＋ `--profile profiles/examples/L2-team-both.json` 生成→ `selfcheck.py` exit 0 のスモーク。

## 4. 受入基準

1. 対話生成で npm を選び許可ドメインを空 Enter した場合、生成される `settings.json` の `sandbox.network.allowedDomains` と Codex `config.toml` の network domains に `registry.npmjs.org` が含まれる。
2. `--profile` 再生成の出力は本変更の前後で不変（profile の明示値のみ使用）。
3. 生成される allow に `Bash(git log *)` が含まれ、docs/11 の例と一致する。
4. `python3 -m unittest discover -s tests` 全通過、生成→selfcheck exit 0。
