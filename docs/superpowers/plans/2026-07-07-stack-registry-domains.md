# スタック連動レジストリドメイン＋git log 自動許可 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 選択・検出したスタックに応じてパッケージレジストリドメインを対話時の既定値として提案し、読み取り専用の `git log` を自動許可へ加えることで、最小権限を保ったまま生成設定の摩擦を減らす。

**Architecture:** `stacks.py` にスタック→ドメインの純データと `domains_for()`（`commands_for()` と同形）を追加。`questions.py` の純関数 `allowed_domains_question()` が動的既定を持つ質問コピーを返し、`generate.py` の対話フローだけがそれを使う（`--profile` 再生成は不変）。`git log` は `build_claude.py` と docs/11 の例の両方へ追加して正典整合を保つ。

**Tech Stack:** Python 3.11+ 標準ライブラリのみ、`unittest`。

**Spec:** `docs/superpowers/specs/2026-07-07-stack-registry-domains-design.md`

## Global Constraints

- Python 3.11 以上・**標準ライブラリのみ**（`pip install` 禁止）。
- テストは標準 `unittest`。実行: `cd generator && python3 -m unittest discover -s tests`（このリポジトリのルートは `/…/coding-agent-security-work`。以降のコマンドはすべて `generator/` で実行）。
- `agentsec/` はロジックのみ。対話 I/O（input/print）は `generate.py` に閉じ込める。
- `--profile` 再生成の出力は本変更の前後で不変であること（profile の明示値のみ使用）。
- docs の値＝生成設定の一致を維持（docs/07・docs/11 と生成 allow の整合）。
- 改行は LF、ファイル I/O は `encoding="utf-8"`。
- コミットメッセージは英語・Conventional Commits・命令形・小文字始まり・50文字目安。

---

### Task 1: `stacks.py` に `domains` データと `domains_for()` を追加

**Files:**
- Modify: `generator/agentsec/stacks.py`
- Test: `generator/tests/test_stacks.py`

**Interfaces:**
- Produces: `stacks.domains_for(stack_keys: list[str]) -> list[str]`（union・sorted、未知キーは `ValueError`）。`STACKS[key]["domains"]: list[str]`（全スタックに存在）。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_stacks.py` の `TestStacks` クラス末尾に追加:

```python
    def test_npm_domains(self):
        self.assertEqual(stacks.domains_for(["npm"]), ["registry.npmjs.org"])

    def test_multiple_stack_domains_merge_sorted_dedup(self):
        result = stacks.domains_for(["maven", "gradle"])
        # repo.maven.apache.org は重複排除され1回だけ
        self.assertEqual(result,
                         ["plugins.gradle.org", "repo.maven.apache.org"])

    def test_empty_stacks_empty_domains(self):
        self.assertEqual(stacks.domains_for([]), [])

    def test_unknown_stack_domains_raises(self):
        with self.assertRaises(ValueError):
            stacks.domains_for(["cobol"])

    def test_every_stack_has_domains_key(self):
        for key, spec in stacks.STACKS.items():
            self.assertIn("domains", spec, key)
            self.assertTrue(spec["domains"], key)
```

- [ ] **Step 2: 失敗を確認**

Run: `python3 -m unittest tests.test_stacks -v`
Expected: 上記5件が FAIL/ERROR（`KeyError: 'domains'` / `AttributeError: ... 'domains_for'`）

- [ ] **Step 3: 実装**

`generator/agentsec/stacks.py` の `STACKS` 各エントリへ `"domains"` を追加し、`commands_for` の後に `domains_for` を追加:

```python
STACKS = {
    "npm": {
        "allow": ["Bash(npm run lint)", "Bash(npm run test *)", "Bash(npm run build *)"],
        "ask": ["Bash(npm install *)"],
        "domains": ["registry.npmjs.org"],
    },
    "maven": {
        "allow": ["Bash(mvn test *)", "Bash(mvn compile *)"],
        "ask": ["Bash(mvn install *)"],
        "domains": ["repo.maven.apache.org"],
    },
    "gradle": {
        "allow": ["Bash(gradle test *)", "Bash(gradle build *)"],
        "ask": ["Bash(gradle publish *)"],
        "domains": ["repo.maven.apache.org", "plugins.gradle.org"],
    },
    "pip": {
        "allow": ["Bash(pytest *)", "Bash(python -m pytest *)"],
        "ask": ["Bash(pip install *)", "Bash(poetry install *)"],
        "domains": ["pypi.org", "files.pythonhosted.org"],
    },
    "dotnet": {
        "allow": ["Bash(dotnet test *)", "Bash(dotnet build *)"],
        "ask": ["Bash(dotnet restore *)"],
        "domains": ["api.nuget.org"],
    },
    "go": {
        "allow": ["Bash(go test *)", "Bash(go build *)"],
        "ask": ["Bash(go install *)"],
        "domains": ["proxy.golang.org", "sum.golang.org"],
    },
}
```

```python
def domains_for(stack_keys):
    """選択スタックのパッケージレジストリドメインを union・sorted で返す。"""
    domains = set()
    for key in stack_keys:
        if key not in STACKS:
            raise ValueError(f"unknown stack: {key}")
        domains.update(STACKS[key]["domains"])
    return sorted(domains)
```

- [ ] **Step 4: テスト通過を確認**

Run: `python3 -m unittest tests.test_stacks -v`
Expected: 全件 PASS

- [ ] **Step 5: 回帰確認**

Run: `python3 -m unittest discover -s tests`
Expected: `OK`（147 tests）

- [ ] **Step 6: コミット**

```bash
git add agentsec/stacks.py tests/test_stacks.py
git commit -m "feat: map stacks to package registry domains

Co-authored-by: Claude <noreply@anthropic.com>"
```

---

### Task 2: `questions.allowed_domains_question()`（動的既定の質問コピー）

**Files:**
- Modify: `generator/agentsec/questions.py`
- Test: `generator/tests/test_questions.py`

**Interfaces:**
- Consumes: `stacks.domains_for(stack_keys)`（Task 1）、`rules.DEFAULT_ALLOWED_DOMAINS`。
- Produces: `questions.allowed_domains_question(stack_keys: list[str]) -> dict` — `QUESTIONS` の `allowed_domains` 質問の**コピー**に、`default` = `DEFAULT_ALLOWED_DOMAINS` ＋ スタック由来ドメイン（DEFAULT を先頭・重複排除）と、動的既定を反映した `detail` を設定して返す。元の `QUESTIONS` は変異しない。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_questions.py` の `TestQuestions` クラス末尾に追加:

```python
    def test_allowed_domains_question_includes_stack_registries(self):
        q = questions.allowed_domains_question(["npm"])
        self.assertEqual(q["key"], "allowed_domains")
        for d in rules.DEFAULT_ALLOWED_DOMAINS:
            self.assertIn(d, q["default"])
        self.assertIn("registry.npmjs.org", q["default"])
        # DEFAULT が先頭を維持
        self.assertEqual(q["default"][:len(rules.DEFAULT_ALLOWED_DOMAINS)],
                         list(rules.DEFAULT_ALLOWED_DOMAINS))
        # detail に動的既定が反映される
        self.assertIn("registry.npmjs.org", q["detail"])

    def test_allowed_domains_question_empty_stacks_is_base_default(self):
        q = questions.allowed_domains_question([])
        self.assertEqual(q["default"], list(rules.DEFAULT_ALLOWED_DOMAINS))

    def test_allowed_domains_question_does_not_mutate_questions(self):
        before = list(self._q("allowed_domains")["default"])
        questions.allowed_domains_question(["npm"])
        self.assertEqual(self._q("allowed_domains")["default"], before)

    def test_allowed_domains_question_empty_answer_uses_dynamic_default(self):
        q = questions.allowed_domains_question(["pip"])
        status, value = questions.resolve_answer(q, "")
        self.assertEqual(status, "ok")
        self.assertIn("pypi.org", value)
```

- [ ] **Step 2: 失敗を確認**

Run: `python3 -m unittest tests.test_questions -v`
Expected: 上記4件が ERROR（`AttributeError: ... 'allowed_domains_question'`）

- [ ] **Step 3: 実装**

`generator/agentsec/questions.py` の `QUESTIONS` 定義の後（`_default_display` の前）に追加:

```python
def allowed_domains_question(stack_keys):
    """allowed_domains 質問のコピーへスタック連動の既定値を設定して返す。"""
    q = dict(next(q for q in QUESTIONS if q["key"] == "allowed_domains"))
    extra = [d for d in stacks.domains_for(stack_keys)
             if d not in rules.DEFAULT_ALLOWED_DOMAINS]
    default = list(rules.DEFAULT_ALLOWED_DOMAINS) + extra
    q["default"] = default
    q["detail"] = (f"空 Enter で既定 ({', '.join(default)}) を採用します。"
                   "既定には選択スタックのパッケージレジストリを含みます。"
                   "ここに無いドメインへの接続は遮断されます。")
    return q
```

- [ ] **Step 4: テスト通過を確認**

Run: `python3 -m unittest tests.test_questions -v`
Expected: 全件 PASS

- [ ] **Step 5: 回帰確認**

Run: `python3 -m unittest discover -s tests`
Expected: `OK`

- [ ] **Step 6: コミット**

```bash
git add agentsec/questions.py tests/test_questions.py
git commit -m "feat: derive allowed-domains default from stacks

Co-authored-by: Claude <noreply@anthropic.com>"
```

---

### Task 3: `generate.py` 対話フローの配線

**Files:**
- Modify: `generator/generate.py`（`collect_interactive`、現行 80〜104 行付近）
- Test: `generator/tests/test_generate.py`

**Interfaces:**
- Consumes: `questions.allowed_domains_question(stack_keys)`（Task 2）。
- Produces: 対話フローで許可ドメインを空 Enter した場合、profile の `allowed_domains` にスタック連動既定が入る。`--profile` 経路は不変。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_generate.py` の `TestCollectInteractive` クラス末尾に追加（既存の `scripted` / `sink` ヘルパーを使う。入力順は既存テスト `test_unknown_stack_warns_and_reasks` と同じ）:

```python
    def test_empty_domains_answer_gets_stack_registry_default(self):
        with tempfile.TemporaryDirectory() as d:
            # 製品2, level, plan, stacks, domains(空Enter), extra, container,
            # 4 redline, base-image 採用
            inputs = ["y", "y", "L2", "team",
                      "npm",
                      "", "",
                      "y", "n", "n", "n", "n",
                      ""]
            out, pr = sink()
            profile = generate.collect_interactive(scripted(inputs), pr, target_dir=d)
            self.assertIn("registry.npmjs.org", profile["allowed_domains"])
            self.assertIn("github.com", profile["allowed_domains"])

    def test_explicit_domains_answer_overrides_dynamic_default(self):
        with tempfile.TemporaryDirectory() as d:
            inputs = ["y", "y", "L2", "team",
                      "npm",
                      "registry.company.example", "",
                      "y", "n", "n", "n", "n",
                      ""]
            out, pr = sink()
            profile = generate.collect_interactive(scripted(inputs), pr, target_dir=d)
            self.assertEqual(profile["allowed_domains"], ["registry.company.example"])
```

- [ ] **Step 2: 失敗を確認**

Run: `python3 -m unittest tests.test_generate.TestCollectInteractive -v`
Expected: `test_empty_domains_answer_gets_stack_registry_default` が FAIL（`registry.npmjs.org` が入らない）。`test_explicit_domains_answer_overrides_dynamic_default` は PASS でよい。

- [ ] **Step 3: 実装**

`generator/generate.py` の `collect_interactive` のループを変更:

```python
    a = {}
    for q in questions.QUESTIONS:
        if q["key"] == "stacks":
            a["stacks"] = resolve_stacks_interactive(target_dir, input_fn, print_fn)
        elif q["key"] == "allowed_domains":
            dq = questions.allowed_domains_question(a["stacks"])
            a["allowed_domains"] = ask_question(dq, input_fn, print_fn)
        else:
            a[q["key"]] = ask_question(q, input_fn, print_fn)
```

（`allowed_domains` は `QUESTIONS` 上で `stacks` の直後にあり、`a["stacks"]` は確定済み。）

- [ ] **Step 4: テスト通過を確認**

Run: `python3 -m unittest tests.test_generate -v`
Expected: 全件 PASS

- [ ] **Step 5: 回帰確認**

Run: `python3 -m unittest discover -s tests`
Expected: `OK`

- [ ] **Step 6: コミット**

```bash
git add generate.py tests/test_generate.py
git commit -m "feat: propose stack registry domains in interactive flow

Co-authored-by: Claude <noreply@anthropic.com>"
```

---

### Task 4: `git log` を生成 allow へ追加

**Files:**
- Modify: `generator/agentsec/build_claude.py:20`（`build_settings` の allow）、`generator/agentsec/build_claude.py:50`（`build_managed_settings` の allow）
- Test: `generator/tests/test_build_claude.py`

**Interfaces:**
- Produces: `build_settings(...)["permissions"]["allow"]` / `build_managed_settings(...)["permissions"]["allow"]` に `"Bash(git log *)"` が含まれる。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_build_claude.py` の `TestBuildClaude` クラス末尾に追加:

```python
    def test_settings_allow_readonly_git_commands(self):
        s = build_claude.build_settings("L2", [], ["github.com"], [])
        for cmd in ("Bash(git status)", "Bash(git diff *)", "Bash(git log *)"):
            self.assertIn(cmd, s["permissions"]["allow"])

    def test_managed_allow_readonly_git_commands(self):
        m = build_claude.build_managed_settings("L3", [], ["github.com"], [], [])
        for cmd in ("Bash(git status)", "Bash(git diff *)", "Bash(git log *)"):
            self.assertIn(cmd, m["permissions"]["allow"])
```

- [ ] **Step 2: 失敗を確認**

Run: `python3 -m unittest tests.test_build_claude -v`
Expected: 上記2件が FAIL（`Bash(git log *)` 不在）

- [ ] **Step 3: 実装**

`generator/agentsec/build_claude.py` の2箇所を変更:

```python
            "allow": cmds["allow"] + ["Bash(git status)", "Bash(git diff *)",
                                      "Bash(git log *)"],
```

（`build_settings` 内。`build_managed_settings` 内も同様に）

```python
            "allow": ["Bash(git status)", "Bash(git diff *)", "Bash(git log *)"],
```

- [ ] **Step 4: テスト通過を確認**

Run: `python3 -m unittest tests.test_build_claude -v`
Expected: 全件 PASS

- [ ] **Step 5: 回帰確認**

Run: `python3 -m unittest discover -s tests`
Expected: `OK`

- [ ] **Step 6: コミット**

```bash
git add agentsec/build_claude.py tests/test_build_claude.py
git commit -m "feat: auto-allow read-only git log in generated settings

Co-authored-by: Claude <noreply@anthropic.com>"
```

---

### Task 5: docs/11 の整合更新とスモーク検証

**Files:**
- Modify: `docs/11-claude-code.md`（11.4 の allow 例＝82行付近、11.5 の allow 例＝158行付近、11.4 直後の生成ツール注記＝129行付近）

**Interfaces:**
- Consumes: Task 1〜4 の生成挙動（docs の記述を実装と一致させる）。

- [ ] **Step 1: 11.4 の settings.json 例へ `git log` を追加**

`docs/11-claude-code.md` の 11.4 例（82行付近）:

```json
      "Bash(git diff *)",
      "WebFetch(domain:docs.company.example)"
```

を次に変更:

```json
      "Bash(git diff *)",
      "Bash(git log *)",
      "WebFetch(domain:docs.company.example)"
```

- [ ] **Step 2: 11.5 の managed-settings.json 例へ `git log` を追加**

11.5 例（158行付近）:

```json
      "Bash(git status)",
      "Bash(git diff *)",
      "WebFetch(domain:docs.company.example)"
```

を次に変更:

```json
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "WebFetch(domain:docs.company.example)"
```

- [ ] **Step 3: 11.4 直後の生成ツール注記へレジストリドメイン提案を追記**

129行付近の段落:

```markdown
生成ツール（`generator/`）の `settings.json` は摩擦の小さい明示列挙（`~/.ssh`・`~/.aws`・`~/.kube`）を既定とする。上記の `~/` 全遮断はより強い代替であり、案件要件に応じて手動で切り替える。
```

の直後（同段落末尾）に追記して次の形にする:

```markdown
生成ツール（`generator/`）の `settings.json` は摩擦の小さい明示列挙（`~/.ssh`・`~/.aws`・`~/.kube`）を既定とする。上記の `~/` 全遮断はより強い代替であり、案件要件に応じて手動で切り替える。また生成ツールは、選択したスタックに応じてパッケージレジストリドメイン（例: npm → `registry.npmjs.org`）を `allowedDomains` の既定として対話時に提案する（提案であり、対話中に編集できる）。
```

- [ ] **Step 4: スモーク検証（受入基準1・2・4）**

```bash
cd generator
python3 -m unittest discover -s tests
python3 generate.py --profile profiles/examples/L2-team-both.json --output /tmp/gen-smoke --force
python3 /tmp/gen-smoke/acceptance/selfcheck.py /tmp/gen-smoke
```

Expected: テスト `OK`、生成 6 件、selfcheck exit 0。さらに profile 再生成の出力に `registry.npmjs.org` が**含まれない**こと（profile の明示値のみ使用）を確認:

```bash
grep -r "registry.npmjs.org" /tmp/gen-smoke && echo "UNEXPECTED" || echo "OK: profile values untouched"
```

Expected: `OK: profile values untouched`

- [ ] **Step 5: コミット**

```bash
cd ..
git add docs/11-claude-code.md
git commit -m "docs: align claude code examples with git log allow

Add git log to allow examples per docs/07 7.1 and note that
the generator proposes stack registry domains interactively.

Co-authored-by: Claude <noreply@anthropic.com>"
```
