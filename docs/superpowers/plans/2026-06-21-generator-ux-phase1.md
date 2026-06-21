# Generator UX 改善 フェーズ1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 非専門の現場メンバーが案件ごとに迷わず設定を生成できるよう、対話に説明・既定値・詳細ヘルプを与え、生成物に自己説明（ヘッダ／README）を付け、プロファイル保存・上書き保護・入力確認を追加する。

**Architecture:** 純粋なデータ・ロジック（質問定義、回答解釈、サマリ整形、バナー文、README 整形、スタック検証）は `agentsec/` に置きユニットテストする。対話 I/O は `generate.py` に閉じ込め、`input`/`print` を関数注入することで統合テスト可能にする。生成物への自己説明はコメント可ファイル（TOML/Dockerfile/compose）へバナーを前置し、コメント不可の JSON は README で補完する。

**Tech Stack:** Python 3.11+ 標準ライブラリのみ、`unittest`、`string.Template`、`pathlib`。

## Global Constraints

- Python 3.11 以上、標準ライブラリのみ。サードパーティ依存を追加しない。
- TOML 書き込みは `agentsec/render_toml.py` を使う（`tomllib` は読み取り専用）。
- `agentsec/selfcheck.py` は standalone を保つ（`from agentsec import ...` を入れない）。生成物へ verbatim コピーされる。
- テストは標準 `unittest`。実行: `cd generator && python3 -m unittest discover -s tests`
- 改行は LF。パス操作は `pathlib`、ファイル I/O は `encoding="utf-8"`。
- `agentsec/` はロジックのみ。対話 I/O は `generate.py` に閉じ込める（関数は引数で値を受け取りテスト可能にする）。
- 新機能・変更時は TDD（失敗するテスト → 実装 → 通過）。
- コミットは英語・Conventional Commits。subject は命令形・小文字始まり・末尾ピリオドなし、おおむね50文字以内。
- ガイドの値（`docs/00-red-lines.md`・`docs/10-codex.md`・`docs/11-claude-code.md`）と生成設定を一致させる。
- 生成物のヘッダ／バナー文には selfcheck の禁止語（`privileged`, `network_mode: host`, `docker.sock`, `/:/host`）を含めない。
- 既定値の方針: レベル=`L2`、プラン=`team`、製品=両方 `y`、コンテナ=`y`、レッドライン4問=`n`（安全側）。
- このフェーズでは自動検出（フェーズ2）と Codex 設定の中身監査（改善8〜11、別計画）は扱わない。

---

## File Structure

新規（`agentsec/`、すべて純ロジック）:
- `agentsec/questions.py` — 対話の質問定義（純データ）と回答解釈・プロンプト整形（純関数）。
- `agentsec/summary.py` — 生成前の入力サマリ整形。
- `agentsec/banner.py` — コメント可ファイルへ前置するヘッダバナー文の生成。
- `agentsec/readme.py` — 生成された成果物に応じた README 用「成果物ガイド」「適用手順」整形。

変更:
- `agentsec/stacks.py` — 既知スタック集合の公開と未知キー検出を追加。
- `agentsec/orchestrate.py` — コメント可ファイルへバナー前置、README の出し分けデータ供給、`output_has_files` 追加、`print` 文の `python3` 化。
- `templates/policy/README.md.tmpl` — 成果物ガイド／適用手順／2フロー／`python3` 化。
- `templates/policy/policy-sheet.md.tmpl` — `python3` 化。
- `generate.py` — `questions` 駆動の対話、`--save-profile`、上書き保護（`--force`）、サマリ確認、未知スタックの親切化。`input`/`print` を注入可能に。

新規テスト:
- `tests/test_questions.py`, `tests/test_summary.py`, `tests/test_banner.py`, `tests/test_readme.py`, `tests/test_generate.py`
- 既存へ追記: `tests/test_stacks.py`, `tests/test_orchestrate.py`

---

## Task 1: スタック未知キー検出

**Files:**
- Modify: `generator/agentsec/stacks.py`
- Test: `generator/tests/test_stacks.py`

**Interfaces:**
- Produces:
  - `stacks.KNOWN: frozenset[str]` — 既知スタックキー集合。
  - `stacks.unknown_keys(keys: list[str]) -> list[str]` — 未知キーのみを入力順で返す。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_stacks.py` の末尾に追記:

```python
    def test_known_contains_all_stack_keys(self):
        self.assertEqual(stacks.KNOWN, frozenset(stacks.STACKS))

    def test_unknown_keys_returns_only_unknown_in_order(self):
        self.assertEqual(stacks.unknown_keys(["npm", "rust", "pip", "ruby"]), ["rust", "ruby"])

    def test_unknown_keys_empty_when_all_known(self):
        self.assertEqual(stacks.unknown_keys(["npm", "pip"]), [])
```

ファイル先頭の import が `from agentsec import stacks` であることを確認（無ければ合わせる）。

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_stacks -v`
Expected: FAIL（`AttributeError: module 'agentsec.stacks' has no attribute 'KNOWN'`）

- [ ] **Step 3: 最小実装**

`generator/agentsec/stacks.py` の `commands_for` 定義の直前（`STACKS` 辞書の後）に追記:

```python
KNOWN = frozenset(STACKS)


def unknown_keys(keys):
    """keys のうち STACKS に無いものを入力順で返す。"""
    return [k for k in keys if k not in STACKS]
```

- [ ] **Step 4: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_stacks -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
cd generator && git add agentsec/stacks.py tests/test_stacks.py
git commit -m "feat: expose known stacks and unknown-key detection"
```

---

## Task 2: 質問定義と回答解釈

**Files:**
- Create: `generator/agentsec/questions.py`
- Test: `generator/tests/test_questions.py`

**Interfaces:**
- Consumes: `rules.LEVELS`, `rules.PLANS`, `rules.DEFAULT_ALLOWED_DOMAINS`, `stacks.KNOWN`
- Produces:
  - `questions.QUESTIONS: list[dict]` — 各要素キー `key, type, prompt, default, help_line, detail`（`type` が `"choice"` のとき `choices` を含む）。`type` は `"yesno" | "choice" | "csv"`。
  - `questions.render_prompt(q: dict) -> str` — 1行説明・既定・`?`案内を含む入力プロンプト文字列。
  - `questions.resolve_answer(q: dict, raw: str) -> tuple[str, object]` — `("help", None)` / `("ok", value)` / `("error", message)`。`value` は yesno→`bool`、choice→`str`、csv→`list[str]`。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_questions.py` を作成:

```python
import unittest
from agentsec import questions, rules


class TestQuestions(unittest.TestCase):
    def _q(self, key):
        return next(q for q in questions.QUESTIONS if q["key"] == key)

    def test_every_question_has_help_and_detail(self):
        for q in questions.QUESTIONS:
            self.assertTrue(q["help_line"].strip(), q["key"])
            self.assertTrue(q["detail"].strip(), q["key"])
            self.assertIn(q["type"], ("yesno", "choice", "csv"), q["key"])

    def test_level_default_is_l2(self):
        self.assertEqual(self._q("level")["default"], "L2")

    def test_redline_questions_default_to_no(self):
        for key in ("use_full_access", "share_docker_socket", "network_host", "direct_push"):
            self.assertEqual(self._q(key)["default"], "n", key)

    def test_render_prompt_shows_default_and_help(self):
        text = questions.render_prompt(self._q("level"))
        self.assertIn("L2", text)
        self.assertIn("?", text)

    def test_resolve_question_mark_returns_help(self):
        self.assertEqual(questions.resolve_answer(self._q("level"), "?"), ("help", None))

    def test_resolve_empty_uses_default(self):
        self.assertEqual(questions.resolve_answer(self._q("level"), ""), ("ok", "L2"))

    def test_resolve_yesno_to_bool(self):
        self.assertEqual(questions.resolve_answer(self._q("use_full_access"), "y"), ("ok", True))
        self.assertEqual(questions.resolve_answer(self._q("use_full_access"), ""), ("ok", False))

    def test_resolve_choice_validates(self):
        status, msg = questions.resolve_answer(self._q("level"), "L9")
        self.assertEqual(status, "error")
        self.assertIn("L1", msg)

    def test_resolve_csv_splits_and_trims(self):
        self.assertEqual(
            questions.resolve_answer(self._q("stacks"), " npm , pip "),
            ("ok", ["npm", "pip"]))

    def test_resolve_csv_empty_stacks_is_empty_list(self):
        self.assertEqual(questions.resolve_answer(self._q("stacks"), ""), ("ok", []))

    def test_resolve_csv_empty_domains_uses_default(self):
        self.assertEqual(
            questions.resolve_answer(self._q("allowed_domains"), ""),
            ("ok", list(rules.DEFAULT_ALLOWED_DOMAINS)))
```

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_questions -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'agentsec.questions'`）

- [ ] **Step 3: 最小実装**

`generator/agentsec/questions.py` を作成:

```python
"""対話の質問定義（純データ）と回答解釈・プロンプト整形（純ロジック）。

対話 I/O（input/print）は generate.py に置く。ここは引数で値を受け取り
テスト可能な純関数のみを提供する。
"""

from agentsec import rules, stacks

_STACK_LIST = ", ".join(sorted(stacks.KNOWN))

QUESTIONS = [
    {"key": "include_claude", "type": "yesno", "default": "y",
     "prompt": "Claude Code を対象に含めますか",
     "help_line": "Claude Code 用の設定を生成します。",
     "detail": "settings.json（team かつ L3+ では managed-settings.json も）を出力します。"},
    {"key": "include_codex", "type": "yesno", "default": "y",
     "prompt": "Codex を対象に含めますか",
     "help_line": "Codex 用の設定を生成します。",
     "detail": "config.toml（team では requirements.toml も）を出力します。"},
    {"key": "level", "type": "choice", "choices": list(rules.LEVELS), "default": "L2",
     "prompt": "利用レベル",
     "help_line": "与える権限の段階。番号が大きいほど制限が強い。",
     "detail": ("L1=計画/読み取り中心の最小権限。L2=ワークスペース編集ありの標準。"
                "L3=組織の強制設定を適用。L4=Web 検索も遮断する最も厳格な構成。迷ったら L2。")},
    {"key": "plan", "type": "choice", "choices": list(rules.PLANS), "default": "team",
     "prompt": "契約プラン",
     "help_line": "個人契約(personal)か、チーム/ビジネス契約(team)か。",
     "detail": ("team かつ L3+ のときのみ組織強制設定"
                "（managed-settings.json / requirements.toml）を生成します。")},
    {"key": "stacks", "type": "csv", "default": "",
     "prompt": "ビルド/言語スタック（カンマ区切り、無ければ空 Enter）",
     "help_line": f"対象プロジェクトで使うものを選びます。対応: {_STACK_LIST}。",
     "detail": ("ここで挙げたスタックの test/build 等を許可コマンドに追加します。"
                f"対応 = {_STACK_LIST}。未対応のものは空のままにし、生成後に手動で追加してください。")},
    {"key": "allowed_domains", "type": "csv",
     "default": list(rules.DEFAULT_ALLOWED_DOMAINS),
     "prompt": "許可するネットワークドメイン（カンマ区切り）",
     "help_line": "エージェントが接続してよいドメインだけを列挙します。",
     "detail": ("空 Enter で既定 "
                f"({', '.join(rules.DEFAULT_ALLOWED_DOMAINS)}) を採用します。"
                "ここに無いドメインへの接続は遮断されます。")},
    {"key": "extra_deny_paths", "type": "csv", "default": "",
     "prompt": "追加で読み取り禁止にするパス（カンマ区切り、無ければ空 Enter）",
     "help_line": "既定の .env / secrets に加えて読み取りを禁止したいパス。",
     "detail": "例: **/keys/**, ./private/**。空 Enter なら既定の機密パスのみを禁止します。"},
    {"key": "use_container", "type": "yesno", "default": "y",
     "prompt": "コンテナ定義（Dockerfile 等）を出力しますか",
     "help_line": "非 root・最小権限のコンテナ定義一式を生成します。",
     "detail": "Dockerfile / docker-compose.yml / .devcontainer / .dockerignore を出力します。"},
    {"key": "use_full_access", "type": "yesno", "default": "n",
     "prompt": "権限バイパス/フルアクセスを常用しますか",
     "help_line": "（レッドライン）原則いいえ。安全側の既定は n。",
     "detail": ("はいにすると承認なしで任意コマンドを実行でき、隔離の意味が失われます。"
                "docs/00-red-lines.md の MUST 違反。既定の n を推奨。")},
    {"key": "share_docker_socket", "type": "yesno", "default": "n",
     "prompt": "コンテナへ Docker ソケットを共有しますか",
     "help_line": "（レッドライン）原則いいえ。安全側の既定は n。",
     "detail": ("ホストの Docker デーモンを操作できるようになり、実質ホスト root 相当の"
                "奪取が可能になります。docs/00-red-lines.md の MUST 違反。既定の n を推奨。")},
    {"key": "network_host", "type": "yesno", "default": "n",
     "prompt": "ホストネットワークを使用しますか",
     "help_line": "（レッドライン）原則いいえ。安全側の既定は n。",
     "detail": ("コンテナのネットワーク隔離が外れ、ホストの localhost や内部サービスへ"
                "到達可能になります。docs/00-red-lines.md の MUST 違反。既定の n を推奨。")},
    {"key": "direct_push", "type": "yesno", "default": "n",
     "prompt": "エージェントに直接 push/deploy を行わせますか",
     "help_line": "（レッドライン）原則いいえ。安全側の既定は n。",
     "detail": ("リモートや本番への変更はエージェント外（人/パイプライン）で行うべきです。"
                "docs/00-red-lines.md の MUST 違反。既定の n を推奨。")},
]


def _default_display(q):
    if q["type"] == "csv":
        d = q["default"]
        if isinstance(d, list):
            return ", ".join(d) if d else "なし"
        return "なし"
    return q["default"]


def render_prompt(q):
    return (f"{q['prompt']} （既定: {_default_display(q)} — {q['help_line']}"
            f" ／ ? で詳細）: ")


def resolve_answer(q, raw):
    raw = raw.strip()
    if raw == "?":
        return ("help", None)

    if q["type"] == "yesno":
        if raw == "":
            raw = q["default"]
        if raw not in ("y", "n"):
            return ("error", "y または n を入力してください")
        return ("ok", raw == "y")

    if q["type"] == "choice":
        if raw == "":
            raw = q["default"]
        if raw not in q["choices"]:
            return ("error", f"次から選んでください: {', '.join(q['choices'])}")
        return ("ok", raw)

    # csv
    if raw == "":
        d = q["default"]
        return ("ok", list(d) if isinstance(d, list) else [])
    return ("ok", [s.strip() for s in raw.split(",") if s.strip()])
```

- [ ] **Step 4: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_questions -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
cd generator && git add agentsec/questions.py tests/test_questions.py
git commit -m "feat: add interactive question definitions and answer parsing"
```

---

## Task 3: 入力サマリ整形

**Files:**
- Create: `generator/agentsec/summary.py`
- Test: `generator/tests/test_summary.py`

**Interfaces:**
- Produces: `summary.format_summary(profile: dict) -> str` — 製品/レベル/プラン/スタック/ドメイン/追加 deny/コンテナ/レッドライン4問を人間可読でまとめた複数行文字列。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_summary.py` を作成:

```python
import unittest
from agentsec import summary


class TestSummary(unittest.TestCase):
    def _profile(self):
        return {"products": ["claude", "codex"], "level": "L2", "plan": "team",
                "stacks": ["npm"], "allowed_domains": ["github.com"],
                "extra_deny_paths": [], "use_container": True,
                "use_full_access": False, "share_docker_socket": False,
                "network_host": False, "direct_push": False}

    def test_summary_contains_core_fields(self):
        text = summary.format_summary(self._profile())
        self.assertIn("L2", text)
        self.assertIn("team", text)
        self.assertIn("claude", text)
        self.assertIn("npm", text)
        self.assertIn("github.com", text)

    def test_summary_shows_none_for_empty_lists(self):
        p = self._profile()
        p["stacks"] = []
        p["extra_deny_paths"] = []
        text = summary.format_summary(p)
        self.assertIn("なし", text)

    def test_summary_reports_redline_answers(self):
        p = self._profile()
        p["network_host"] = True
        text = summary.format_summary(p)
        self.assertIn("ホストネットワーク", text)
        self.assertIn("はい", text)
```

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_summary -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'agentsec.summary'`）

- [ ] **Step 3: 最小実装**

`generator/agentsec/summary.py` を作成:

```python
"""生成前に表示する入力サマリの整形（純関数）。"""

_REDLINE_LABELS = [
    ("use_full_access", "フルアクセス常用"),
    ("share_docker_socket", "Docker ソケット共有"),
    ("network_host", "ホストネットワーク"),
    ("direct_push", "直接 push/deploy"),
]


def _join(items):
    return ", ".join(items) if items else "なし"


def _yn(value):
    return "はい" if value else "いいえ"


def format_summary(profile):
    redlines = "、".join(
        f"{label}={_yn(profile.get(key, False))}"
        for key, label in _REDLINE_LABELS)
    return "\n".join([
        "=== 生成内容の確認 ===",
        f"製品: {_join(profile['products'])}",
        f"レベル: {profile['level']} / プラン: {profile['plan']}",
        f"スタック: {_join(profile['stacks'])}",
        f"許可ドメイン: {_join(profile['allowed_domains'])}",
        f"追加 deny パス: {_join(profile['extra_deny_paths'])}",
        f"コンテナ定義: {'生成する' if profile['use_container'] else '生成しない'}",
        f"レッドライン: {redlines}",
    ])
```

- [ ] **Step 4: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_summary -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
cd generator && git add agentsec/summary.py tests/test_summary.py
git commit -m "feat: add input summary formatting for pre-generation confirm"
```

---

## Task 4: バナー前置（コメント可ファイルの自己説明）

**Files:**
- Create: `generator/agentsec/banner.py`
- Modify: `generator/agentsec/orchestrate.py`
- Test: `generator/tests/test_banner.py`, `generator/tests/test_orchestrate.py`

**Interfaces:**
- Consumes: なし（純関数）
- Produces:
  - `banner.banner(level: str, products: list[str]) -> str` — `#` 始まりの複数行コメント（末尾改行付き）。selfcheck 禁止語を含まない。
  - `orchestrate._write_commentable(out_root, rel, text, head) -> str` — head（バナー）を本文に前置して書き込むヘルパ。

- [ ] **Step 1: 失敗するテストを書く（banner）**

`generator/tests/test_banner.py` を作成:

```python
import unittest
from agentsec import banner

FORBIDDEN = ["privileged", "network_mode: host", "docker.sock", "/:/host"]


class TestBanner(unittest.TestCase):
    def test_banner_is_comment_lines(self):
        for line in banner.banner("L2", ["claude", "codex"]).splitlines():
            self.assertTrue(line.startswith("#"), line)

    def test_banner_mentions_level_and_source_of_truth(self):
        text = banner.banner("L3", ["codex"])
        self.assertIn("L3", text)
        self.assertIn("docs/", text)

    def test_banner_has_no_selfcheck_forbidden_words(self):
        text = banner.banner("L4", ["claude"])
        for needle in FORBIDDEN:
            self.assertNotIn(needle, text)
```

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_banner -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'agentsec.banner'`）

- [ ] **Step 3: 最小実装（banner）**

`generator/agentsec/banner.py` を作成:

```python
"""コメント可ファイル（TOML/Dockerfile/compose）へ前置する自己説明バナー。"""


def banner(level, products):
    prod = ", ".join(products)
    lines = [
        "# === 自動生成: coding-agent-security 設定ジェネレータ ===",
        f"# レベル: {level} / 製品: {prod}",
        "# 値の正典は docs/（00-red-lines.md 等）。変更時は docs と整合させること。",
        "# 再生成すると本ファイルは上書きされます。手元の変更は別管理を。",
    ]
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: 通過を確認（banner）**

Run: `cd generator && python3 -m unittest tests.test_banner -v`
Expected: PASS

- [ ] **Step 5: 失敗するテストを書く（orchestrate でバナー前置）**

`generator/tests/test_orchestrate.py` の `TestOrchestrate` クラス内に追記:

```python
    def test_commentable_files_have_banner(self):
        with tempfile.TemporaryDirectory() as d:
            files = orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            for rel in ("codex/.codex/config.toml", "docker-compose.yml", "Dockerfile"):
                text = Path(files[rel]).read_text(encoding="utf-8")
                self.assertIn("自動生成: coding-agent-security", text)

    def test_json_files_have_no_banner(self):
        with tempfile.TemporaryDirectory() as d:
            files = orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            text = Path(files["claude-code/.claude/settings.json"]).read_text(encoding="utf-8")
            self.assertNotIn("自動生成: coding-agent-security", text)
```

- [ ] **Step 6: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_orchestrate -v`
Expected: FAIL（`test_commentable_files_have_banner` が banner 不在で失敗）

- [ ] **Step 7: 最小実装（orchestrate）**

`generator/agentsec/orchestrate.py` を編集する。

(a) import に banner を追加:

```python
from agentsec import (rules, build_claude, build_codex, render_text, banner,
                      profile as profile_mod)
```

(b) `_write` の直後にヘルパを追加（バナー対象は (d) で明示的に呼び分けるため、定数は持たない）:

```python
def _write_commentable(out_root, rel, text, head):
    return _write(out_root, rel, head + text)
```

(c) `generate` の冒頭、`stacks_keys = profile["stacks"]` の直後に head を作成:

```python
    head = banner.banner(lvl, profile["products"])
```

(d) コメント可ファイルの書き込みを `_write_commentable(..., head)` に変更する。対象は `codex/.codex/config.toml`・`codex/requirements.toml`・`Dockerfile`・`docker-compose.yml` の4箇所。例（config.toml）:

```python
        files["codex/.codex/config.toml"] = _write_commentable(
            output_dir, "codex/.codex/config.toml",
            build_codex.build_config(lvl, stacks_keys, domains, extra), head)
```

同様に `codex/requirements.toml`・`Dockerfile`・`docker-compose.yml` も `_write_commentable(..., head)` にする。JSON（settings.json / managed-settings.json / devcontainer.json / generation-profile.json）と Markdown はそのまま `_write` を使う。

- [ ] **Step 8: 通過を確認（selfcheck PASS も維持）**

Run: `cd generator && python3 -m unittest tests.test_orchestrate tests.test_banner -v`
Expected: PASS（`test_generated_output_passes_selfcheck` を含め全通過）

- [ ] **Step 9: コミット**

```bash
cd generator && git add agentsec/banner.py agentsec/orchestrate.py tests/test_banner.py tests/test_orchestrate.py
git commit -m "feat: prepend self-describing banner to commentable artifacts"
```

---

## Task 5: README/policy-sheet の自己説明と python3 化

**Files:**
- Create: `generator/agentsec/readme.py`
- Modify: `generator/agentsec/orchestrate.py`, `generator/templates/policy/README.md.tmpl`, `generator/templates/policy/policy-sheet.md.tmpl`
- Test: `generator/tests/test_readme.py`, `generator/tests/test_orchestrate.py`

**Interfaces:**
- Consumes: `generate` 内で組み立てた生成ファイルキー集合。
- Produces:
  - `readme.artifact_guide(file_keys: set[str]) -> str` — 生成された成果物のみを役割つきで列挙した Markdown 箇条書き。
  - `readme.apply_steps(file_keys: set[str]) -> str` — 生成された成果物のみに対応する適用手順（存在しないファイルを案内しない）。

- [ ] **Step 1: 失敗するテストを書く（readme）**

`generator/tests/test_readme.py` を作成:

```python
import unittest
from agentsec import readme


class TestReadme(unittest.TestCase):
    def test_guide_lists_only_present_files(self):
        keys = {"claude-code/.claude/settings.json", "codex/.codex/config.toml"}
        text = readme.artifact_guide(keys)
        self.assertIn("settings.json", text)
        self.assertIn("config.toml", text)
        self.assertNotIn("managed-settings.json", text)

    def test_apply_steps_omit_managed_when_absent(self):
        keys = {"claude-code/.claude/settings.json"}
        text = readme.apply_steps(keys)
        self.assertNotIn("managed-settings.json", text)

    def test_apply_steps_include_managed_when_present(self):
        keys = {"claude-code/.claude/settings.json", "claude-code/managed-settings.json"}
        text = readme.apply_steps(keys)
        self.assertIn("managed-settings.json", text)
```

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_readme -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'agentsec.readme'`）

- [ ] **Step 3: 最小実装（readme）**

`generator/agentsec/readme.py` を作成:

```python
"""生成された成果物に応じた README 用テキストの整形（純関数）。

JSON はコメントを持てないため、各成果物の役割と適用手順はここで補完する。
"""

# (相対パス, 役割説明) を生成順に定義。生成されたものだけを出力する。
_ROLES = [
    ("claude-code/.claude/settings.json",
     "Claude Code のプロジェクト設定（補助設定）。リポジトリへ配置。"),
    ("claude-code/managed-settings.json",
     "Claude Code の組織強制設定（team かつ L3+）。リポジトリ外の管理パスへ配置。"),
    ("codex/.codex/config.toml",
     "Codex の開発者設定。先頭コメントの extends 前提を確認のうえ配置。"),
    ("codex/requirements.toml",
     "Codex の組織管理要件（team）。管理側へ配置。"),
    ("Dockerfile", "非 root・最小権限の実行コンテナ定義。"),
    ("docker-compose.yml", "read_only・cap_drop 等を含む起動定義。"),
    (".devcontainer/devcontainer.json", "VS Code devcontainer 定義。"),
    (".dockerignore", "コンテキスト除外設定。"),
    ("acceptance/checklist.md", "受入テストのチェックリスト（docs/15 準拠）。"),
    ("acceptance/selfcheck.py", "レッドラインの静的検査スクリプト（standalone）。"),
    ("POLICY-SHEET.md", "案件別ポリシー記入シート（逸脱を明記）。"),
    ("generation-profile.json", "再現用プロファイル + 各ファイルの SHA-256・逸脱レジスタ。"),
]


def artifact_guide(file_keys):
    lines = [f"- `{rel}` — {role}" for rel, role in _ROLES if rel in file_keys]
    return "\n".join(lines)


def apply_steps(file_keys):
    steps = []
    if "claude-code/.claude/settings.json" in file_keys:
        steps.append("- Claude Code: `claude-code/.claude/settings.json` をリポジトリへ配置")
    if "claude-code/managed-settings.json" in file_keys:
        steps.append("- Claude Code 管理設定: `claude-code/managed-settings.json` を"
                     "リポジトリ外の管理パスへ配置")
    if "codex/.codex/config.toml" in file_keys:
        steps.append("- Codex: `codex/.codex/config.toml` を配置")
    if "codex/requirements.toml" in file_keys:
        steps.append("- Codex 管理要件: `codex/requirements.toml` を管理側へ配置")
    if "Dockerfile" in file_keys:
        steps.append("- コンテナ: `Dockerfile` / `docker-compose.yml` / `.devcontainer/` を利用")
    return "\n".join(steps)
```

- [ ] **Step 4: 通過を確認（readme）**

Run: `cd generator && python3 -m unittest tests.test_readme -v`
Expected: PASS

- [ ] **Step 5: テンプレートを更新**

`generator/templates/policy/README.md.tmpl` を次の内容に置き換える:

```markdown
# 生成された設定の適用手順

- 対象レベル: $level / プラン: $plan / 製品: $products

## このセットの使い方（2つの導入フロー）

- 既存プロジェクトへ導入: 下記「適用」のとおり各ファイルを配置し、`acceptance/checklist.md` で実拒否を確認してから運用を開始する。
- 新規プロジェクトで着工: フォルダだけ作った段階で先に本設定を配置し、ガードレール付きでエージェントを起動する。スタックが固まったら `generation-profile.json` を `--profile` に渡して再生成し、差分を反映する。

## 生成された成果物

$artifact_guide

## 適用

$apply_steps

## 検証（必須）
1. `python3 acceptance/selfcheck.py .` で静的検査（PASS を確認）
2. `acceptance/checklist.md` を実環境で実施し「実拒否」を確認（docs/00 R5）

> selfcheck は静的確認に過ぎません。実拒否は必ず実環境・実バージョンで確認してください。

## 逸脱事項
$deviations_block
```

`generator/templates/policy/policy-sheet.md.tmpl` の検証コマンド参照を `python3` に統一する。`policy-sheet.md.tmpl` に `python ` の記載が無い場合はこの編集はスキップしてよい（現状は記載なし。確認のみ）。

- [ ] **Step 6: 失敗するテストを書く（orchestrate が新キーを渡す）**

`generator/tests/test_orchestrate.py` に追記:

```python
    def test_readme_lists_generated_artifacts_and_uses_python3(self):
        with tempfile.TemporaryDirectory() as d:
            files = orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            text = Path(files["README.md"]).read_text(encoding="utf-8")
            self.assertIn("config.toml", text)
            self.assertIn("python3 acceptance/selfcheck.py", text)

    def test_readme_omits_managed_for_personal_plan(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._profile()
            p["plan"] = "personal"
            files = orchestrate.generate(p, d, [], "node:20-bookworm-slim")
            text = Path(files["README.md"]).read_text(encoding="utf-8")
            self.assertNotIn("managed-settings.json", text)
```

- [ ] **Step 7: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_orchestrate -v`
Expected: FAIL（`KeyError: 'artifact_guide'` テンプレ変数未供給、または旧テンプレ参照で失敗）

- [ ] **Step 8: orchestrate を更新**

`generator/agentsec/orchestrate.py` を編集する。

(a) import に readme を追加:

```python
from agentsec import (rules, build_claude, build_codex, render_text, banner,
                      readme, profile as profile_mod)
```

(b) `text_map` 構築の直前（`files` への README 等の書き込みより前、`text_map = {` の直前）に成果物キー集合を作る。この時点で `files` には設定系・コンテナ系のみが入っているため、必ず生成される受入テスト類・ポリシー・プロファイルを定数で補う:

```python
    artifact_keys = set(files) | {
        "acceptance/checklist.md", "acceptance/selfcheck.py",
        "POLICY-SHEET.md", "generation-profile.json",
    }
```

(c) `text_map` に2キーを追加:

```python
        "artifact_guide": readme.artifact_guide(artifact_keys),
        "apply_steps": readme.apply_steps(artifact_keys),
```

注意: README.md 自身は `_ROLES` に含めていないため一覧には出ない（自己言及を避ける）。上記の補完により、設定・コンテナに加えて `acceptance/checklist.md` 等も「生成された成果物」として案内される。

- [ ] **Step 9: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_orchestrate tests.test_readme -v`
Expected: PASS

- [ ] **Step 10: コミット**

```bash
cd generator && git add agentsec/readme.py agentsec/orchestrate.py templates/policy/README.md.tmpl templates/policy/policy-sheet.md.tmpl tests/test_readme.py tests/test_orchestrate.py
git commit -m "feat: generate artifact-aware README with python3 and apply steps"
```

---

## Task 6: generate.py 統合（対話・保存・保護・確認）

**Files:**
- Modify: `generator/generate.py`
- Test: `generator/tests/test_generate.py`

**Interfaces:**
- Consumes: `questions.QUESTIONS / render_prompt / resolve_answer`, `summary.format_summary`, `stacks.unknown_keys`, `orchestrate.output_has_files`（Task 6 で追加）, `profile.save`, `redlines.check_inputs / has_blocking`。
- Produces:
  - `generate.ask_question(q, input_fn, print_fn) -> object` — `?`でdetail表示、不正で再入力、確定値を返す。
  - `generate.collect_interactive(input_fn, print_fn) -> dict` — questions を回し profile を返す。未知スタックは警告して再入力させる。
  - `generate.confirm(prompt, input_fn, print_fn, default=True) -> bool`
  - `generate.main(argv) -> int` — `--save-profile` / `--force` を追加。

- [ ] **Step 1: orchestrate に `output_has_files` を追加（先に依存を用意）**

`generator/agentsec/orchestrate.py` の `_write` 定義の直後に追加:

```python
def output_has_files(output_dir):
    p = Path(output_dir)
    return p.exists() and any(p.rglob("*"))
```

`generator/tests/test_orchestrate.py` に追記:

```python
    def test_output_has_files_false_for_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(orchestrate.output_has_files(d))

    def test_output_has_files_true_after_generate(self):
        with tempfile.TemporaryDirectory() as d:
            orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            self.assertTrue(orchestrate.output_has_files(d))
```

Run: `cd generator && python3 -m unittest tests.test_orchestrate -v`
Expected: PASS（このステップで `output_has_files` を追加するため）。

- [ ] **Step 2: 失敗するテストを書く（generate）**

`generator/tests/test_generate.py` を作成:

```python
import unittest
import tempfile
import json
from pathlib import Path
import generate
from agentsec import questions


def scripted(inputs):
    it = iter(inputs)
    return lambda prompt="": next(it)


def sink():
    out = []
    return out, (lambda *a, **k: out.append(" ".join(str(x) for x in a)))


class TestAskQuestion(unittest.TestCase):
    def _q(self, key):
        return next(q for q in questions.QUESTIONS if q["key"] == key)

    def test_help_then_value(self):
        out, pr = sink()
        val = generate.ask_question(self._q("level"), scripted(["?", "L3"]), pr)
        self.assertEqual(val, "L3")
        self.assertTrue(any("迷ったら L2" in line for line in out))

    def test_invalid_then_default(self):
        out, pr = sink()
        val = generate.ask_question(self._q("level"), scripted(["L9", ""]), pr)
        self.assertEqual(val, "L2")


class TestCollectInteractive(unittest.TestCase):
    def test_unknown_stack_warns_and_reasks(self):
        # 製品2, level, plan, stacks(不正→正), domains, extra, container, redline*4
        inputs = ["y", "y", "L2", "team",
                  "npm,rust", "npm",          # stacks: 未知 rust → 再入力
                  "github.com", "",
                  "y", "n", "n", "n", "n"]
        out, pr = sink()
        profile = generate.collect_interactive(scripted(inputs), pr)
        self.assertEqual(profile["stacks"], ["npm"])
        self.assertTrue(any("rust" in line for line in out))
        self.assertEqual(profile["level"], "L2")
        self.assertEqual(profile["products"], ["claude", "codex"])


class TestMainSaveProfile(unittest.TestCase):
    def test_save_profile_roundtrips(self):
        with tempfile.TemporaryDirectory() as d:
            prof_path = Path(d) / "p.json"
            src = {"products": ["claude"], "level": "L2", "plan": "personal",
                   "stacks": ["npm"], "allowed_domains": ["github.com"],
                   "extra_deny_paths": [], "use_container": False}
            (Path(d) / "in.json").write_text(json.dumps(src), encoding="utf-8")
            rc = generate.main(["--profile", str(Path(d) / "in.json"),
                                "--output", str(Path(d) / "out"),
                                "--save-profile", str(prof_path)])
            self.assertEqual(rc, 0)
            saved = json.loads(prof_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["level"], "L2")


class TestMainOverwriteGuard(unittest.TestCase):
    def test_nonempty_output_without_force_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            out.mkdir()
            (out / "existing.txt").write_text("x", encoding="utf-8")
            (Path(d) / "in.json").write_text(json.dumps(
                {"products": ["claude"], "level": "L2", "plan": "personal",
                 "stacks": ["npm"], "allowed_domains": ["github.com"],
                 "extra_deny_paths": [], "use_container": False}), encoding="utf-8")
            rc = generate.main(["--profile", str(Path(d) / "in.json"),
                                "--output", str(out)])
            self.assertEqual(rc, 2)
```

- [ ] **Step 3: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_generate -v`
Expected: FAIL（`AttributeError: module 'generate' has no attribute 'ask_question'` 等）

- [ ] **Step 4: generate.py を書き換える**

`generator/generate.py` を次の内容に置き換える:

```python
"""対話 / --profile 再生で設定一式を生成する CLI。

純ロジックは agentsec 側にあり、ここは I/O 配線に徹する。input/print は
引数で注入可能にしてテストできるようにする。
"""

import argparse
import sys
from datetime import date

from agentsec import (rules, redlines, orchestrate, questions, summary, stacks,
                      profile as profile_mod)


def ask_question(q, input_fn=input, print_fn=print):
    while True:
        raw = input_fn(questions.render_prompt(q))
        status, value = questions.resolve_answer(q, raw)
        if status == "help":
            print_fn(f"  {q['detail']}")
            continue
        if status == "error":
            print_fn(f"  {value}")
            continue
        return value


def _answers(input_fn, print_fn):
    return {q["key"]: ask_question(q, input_fn, print_fn) for q in questions.QUESTIONS}


def collect_interactive(input_fn=input, print_fn=print):
    a = {}
    for q in questions.QUESTIONS:
        if q["key"] == "stacks":
            while True:
                chosen = ask_question(q, input_fn, print_fn)
                unknown = stacks.unknown_keys(chosen)
                if not unknown:
                    a["stacks"] = chosen
                    break
                print_fn(f"  未対応のスタックです: {', '.join(unknown)}。"
                         f"対応: {', '.join(sorted(stacks.KNOWN))}。"
                         f"未対応分は空にして生成後に手動追加してください。")
        else:
            a[q["key"]] = ask_question(q, input_fn, print_fn)

    products = []
    if a["include_claude"]:
        products.append("claude")
    if a["include_codex"]:
        products.append("codex")
    return {
        "products": products, "level": a["level"], "plan": a["plan"],
        "stacks": a["stacks"], "allowed_domains": a["allowed_domains"],
        "extra_deny_paths": a["extra_deny_paths"], "use_container": a["use_container"],
        "use_full_access": a["use_full_access"],
        "share_docker_socket": a["share_docker_socket"],
        "network_host": a["network_host"], "direct_push": a["direct_push"],
    }


def confirm(prompt, input_fn=input, print_fn=print, default=True):
    suffix = " [Y/n]: " if default else " [y/N]: "
    raw = input_fn(prompt + suffix).strip().lower()
    if raw == "":
        return default
    return raw == "y"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile")
    parser.add_argument("--output", default="./generated")
    parser.add_argument("--base-image", default="node:20-bookworm-slim")
    parser.add_argument("--allow-redline-override", action="store_true")
    parser.add_argument("--approver", default="")
    parser.add_argument("--save-profile")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.profile:
        profile = profile_mod.load(args.profile)
    else:
        profile = collect_interactive()
        print(summary.format_summary(profile))
        if not confirm("この内容で生成しますか"):
            print("中止しました。")
            return 1

    if args.save_profile:
        profile_mod.save(args.save_profile, profile)
        print(f"プロファイルを保存しました: {args.save_profile}")

    if orchestrate.output_has_files(args.output) and not args.force:
        if args.profile:
            print(f"出力先 {args.output} は空ではありません。"
                  f"上書きするには --force を指定してください。")
            return 2
        if not confirm(f"出力先 {args.output} は空ではありません。上書きしますか",
                       default=False):
            print("中止しました。")
            return 1

    devs = redlines.check_inputs(
        profile["level"], profile["plan"],
        use_full_access=profile.get("use_full_access", False),
        share_docker_socket=profile.get("share_docker_socket", False),
        network_host=profile.get("network_host", False),
        direct_push=profile.get("direct_push", False))
    if redlines.has_blocking(devs, override=args.allow_redline_override):
        print("レッドライン違反のため生成を中止します:")
        for d in devs:
            print(f"  - {d['rule_ref']}: {d['chosen']} (推奨: {d['recommended']})")
        print("続行するには --allow-redline-override と --approver を指定してください。")
        return 2
    if args.allow_redline_override and devs and not args.approver.strip():
        print("エラー: --allow-redline-override 使用時は --approver を指定してください。")
        return 2
    for d in devs:
        d["approver"] = args.approver
        d["date"] = date.today().isoformat()

    files = orchestrate.generate(profile, args.output, devs, args.base_image)
    print(f"{len(files)} 件を {args.output} に生成しました。")
    print("検証: python3 acceptance/selfcheck.py", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_generate -v`
Expected: PASS

- [ ] **Step 6: 全体テストとスモークを確認**

Run:
```bash
cd generator && python3 -m unittest discover -s tests
python3 generate.py --profile profiles/examples/L2-team-both.json --output /tmp/gen-smoke --force
python3 /tmp/gen-smoke/acceptance/selfcheck.py /tmp/gen-smoke
```
Expected: 全テスト PASS、生成成功、selfcheck が exit 0（PASS 表示）。

- [ ] **Step 7: コミット**

```bash
cd generator && git add generate.py agentsec/orchestrate.py tests/test_generate.py tests/test_orchestrate.py
git commit -m "feat: add guided prompts, profile save, and overwrite guard to CLI"
```

---

## Task 7: リポジトリ衛生（生成物のワークツリー除去）

**Files:**
- Delete: `generator/generated/`（ワークツリー上の生成物）
- Verify: `generator/README.md`, `README.md`（ルート）

- [ ] **Step 1: 現状確認**

Run: `cd /Users/a160341/Documents/_work/coding-agent-security-work && git status --porcelain generator/generated && git check-ignore generator/generated`
Expected: `generated/` は `.gitignore` 済みで追跡対象外（`git check-ignore` が該当パスを出力）。

- [ ] **Step 2: ワークツリーから物理削除**

Run: `cd /Users/a160341/Documents/_work/coding-agent-security-work && rm -rf generator/generated`

- [ ] **Step 3: ドキュメントの出力先が /tmp 系であることを確認**

`generator/README.md` のクイックスタートは説明用に `./generated` を例示している。これは案内として残してよい（`.gitignore` 済み）。AGENTS.md / ルート README のスモーク手順が `/tmp/gen-smoke` を使うことを確認する（既にそうなっている）。変更不要なら本ステップはスキップ。

- [ ] **Step 4: 最終確認（コミット対象なし）**

Run: `cd /Users/a160341/Documents/_work/coding-agent-security-work && git status --porcelain`
Expected: 追跡ファイルに変更なし（`generated/` は ignore 済みのため status に出ない）。コミット不要。

---

## Self-Review（計画作成者によるチェック結果）

**Spec coverage（合意した改善 → タスク対応）:**
- 課題1（各問の意味説明）/ 課題2（推奨・既定表示）→ Task 2（`help_line`/`detail`/`default`/`render_prompt`）+ Task 6（`?`でdetail表示・既定採用）。
- 課題3（スタック簡略化）はフェーズ2（別計画）。本フェーズでは Task 1 + Task 6 で未知スタックの親切化のみ対応。
- 課題4（生成物の説明）→ Task 4（コメント可ファイルのバナー）+ Task 5（JSON は README 補完・出し分け）。
- レッドライン4問の既定「いいえ」＋詳細 → Task 2。
- 改善1（--save-profile）→ Task 6。
- 改善2（上書き保護）→ Task 6（`output_has_files` + `--force`）。
- 改善3（生成前サマリ確認）→ Task 3 + Task 6。
- 改善4（未知スタックの親切化）→ Task 1 + Task 6。
- 改善5（python3 表記）→ Task 5（テンプレ）+ Task 6（CLI の print）。
- 改善6（存在しないファイルを案内しない）→ Task 5（`apply_steps`）。
- 改善13（generated/ 除去）→ Task 7。
- 別計画送り: フェーズ2＝自動検出・改善12（base-image 推定）。docs 整合監査＝改善7/8/9/10/11。

**Placeholder scan:** 各コード/テスト/コマンドは実体を記載済み。"TBD"/"適宜"等なし。

**Type consistency:** `resolve_answer` の戻りは `(status, value)` で全タスク一貫。`ask_question` は確定 `value` を返す。`collect_interactive` の出力 profile キーは `profile.REQUIRED_KEYS`（products/level/plan/stacks/allowed_domains/extra_deny_paths/use_container）+ optional bool 4種を満たす。`artifact_guide`/`apply_steps` は `set[str]` を受け取り、`orchestrate` は `set(files)` を渡す。`banner.banner(level, products)` の引数順は呼び出し側と一致。
