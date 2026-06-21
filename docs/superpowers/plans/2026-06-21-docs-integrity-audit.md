# docs 整合監査パス Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** generator の selfcheck を Codex 設定検査＋生成漏れ検出へ拡張し、あわせて Codex network の冗長整理・policy-sheet 連番化・配置ガイド追記を行う。

**Architecture:** `agentsec/selfcheck.py` に純関数 `_check_codex_config` / `_check_codex_requirements` / `_check_completeness` を追加し `check_dir` から呼ぶ。`tomllib`（標準・読取専用）で Codex TOML を解析。生成漏れは `generation-profile.json` の profile から期待ファイル集合を独立導出して欠落を FAIL。`build_codex.py` の network 構築を1回代入へ整理（挙動不変）。`policy-sheet.md.tmpl` を連番化し、`readme.placement_guide` にモノレポ配置注記を足す。

**Tech Stack:** Python 3.11+ 標準ライブラリのみ、標準 `unittest`。

**設計仕様:** `docs/superpowers/specs/2026-06-21-docs-integrity-audit-design.md`

## Global Constraints

- Python 3.11+・標準ライブラリのみ。サードパーティ依存を追加しない。
- TOML 読み取りは `tomllib`。書き込みは追加しない（`render_toml` のまま）。
- `agentsec/selfcheck.py` は standalone を維持（`from agentsec import ...` を入れない。生成物へ verbatim コピーされ単体実行されるため）。`import tomllib` は可。
- selfcheck の戻り規約は `(code, msgs)`：FAIL を含めば code=2、なければ 0。`FAIL ` 前置の行で判定。
- selfcheck は静的確認に過ぎない（実拒否は受入テストで確認する旨の注記を維持。挙動・コメントとも削らない）。
- ドメイン値は docs（`00-red-lines.md`・`10-codex.md`）と一致させる。
- 改行 LF、パスは `pathlib`、ファイル I/O は `encoding="utf-8"`。
- テストは `cd generator && python3 -m unittest discover -s tests`。TDD（失敗するテスト→実装→通過）。
- コミットは英語・Conventional Commits。共著表記:

  ```
  Co-authored-by: Claude <noreply@anthropic.com>
  ```

---

## File Structure

- `generator/agentsec/selfcheck.py`（変更）— Task 1/2/3。Codex 検査・完全性検査を追加。
- `generator/tests/test_selfcheck.py`（変更）— Task 1/2/3 のテスト。
- `generator/agentsec/build_codex.py`（変更）— Task 4。network 整理（F2）＋ web_search コメント（F3）。
- `generator/tests/test_build_codex.py`（変更）— Task 4 の特性テスト。
- `generator/templates/policy/policy-sheet.md.tmpl`（変更）— Task 5。連番化（F1）。
- `generator/agentsec/readme.py`（変更）— Task 5。placement_guide 追記。
- `generator/tests/test_readme.py`（変更）— Task 5 の placement テスト。
- `generator/tests/test_policy_sheet.py`（新規）— Task 5 の連番テスト。

---

## Task 1: selfcheck に Codex config 検査を追加（F4a）

**Files:**
- Modify: `generator/agentsec/selfcheck.py`
- Test: `generator/tests/test_selfcheck.py`

**Interfaces:**
- Consumes: 既存 `check_dir(output_dir) -> (code, msgs)`、`Path`、`json`（既 import）。
- Produces: `_check_codex_config(path, msgs)`（戻り値なし、`msgs` に `FAIL ...` を追記）。`check_dir` が `codex/.codex/config.toml` を検査するようになる。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_selfcheck.py` の末尾に追記する。

```python
class TestCodexConfig(unittest.TestCase):
    _L2 = (
        'approval_policy = "on-request"\n'
        'web_search = "cached"\n'
        'default_permissions = "business-workspace"\n'
        '[permissions.business-workspace]\n'
        'extends = ":workspace"\n'
        '[permissions.business-workspace.filesystem.":workspace_roots"]\n'
        '"**/.env" = "deny"\n'
        '".devcontainer" = "read"\n'
    )

    def test_clean_l2_config_passes(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml", self._L2)
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)

    def test_danger_full_access_default_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'approval_policy = "on-request"\n'
                   'default_permissions = ":danger-full-access"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("R3" in m for m in msgs))

    def test_danger_full_access_extends_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'approval_policy = "on-request"\n'
                   'default_permissions = "x"\n'
                   '[permissions.x]\n'
                   'extends = ":danger-full-access"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("R3" in m for m in msgs))

    def test_approval_never_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'approval_policy = "never"\n'
                   'default_permissions = ":read-only"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("10.8" in m for m in msgs))

    def test_workspace_write_missing_env_deny_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'default_permissions = "business-workspace"\n'
                   '[permissions.business-workspace]\n'
                   'extends = ":workspace"\n'
                   '[permissions.business-workspace.filesystem.":workspace_roots"]\n'
                   '".devcontainer" = "read"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("R2" in m for m in msgs))

    def test_l1_read_only_skips_env_check(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/.codex/config.toml",
                   'approval_policy = "on-request"\n'
                   'web_search = "cached"\n'
                   'default_permissions = ":read-only"\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `cd generator && python3 -m unittest tests.test_selfcheck -v`
Expected: `TestCodexConfig` の各テストが FAIL（config.toml が未検査のため danger-full-access 等でも code=0 になる）。

- [ ] **Step 3: 実装する**

`generator/agentsec/selfcheck.py` の先頭 import に `tomllib` を追加：

```python
import sys
import json
import tomllib
from pathlib import Path
```

`_check_profile` の下（`check_dir` の上）に追加：

```python
def _check_codex_config(path, msgs):
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("default_permissions") == ":danger-full-access":
        msgs.append(f"FAIL {path}: default_permissions が :danger-full-access (00 R3)")
    if data.get("approval_policy") == "never":
        msgs.append(f"FAIL {path}: approval_policy = never (10.8)")
    perms = data.get("permissions", {})
    for name, prof in perms.items():
        if not isinstance(prof, dict):
            continue
        if prof.get("extends") == ":danger-full-access":
            msgs.append(f"FAIL {path}: permissions.{name} が :danger-full-access を継承 (00 R3)")
        # workspace-write プロファイルがあるときのみ .env read deny を要求。
        # L1 の :read-only は permissions を持たずここに来ない（docs 10.3.1: 外部境界で遮断）。
        roots = prof.get("filesystem", {}).get(":workspace_roots", {})
        if roots and not any(".env" in k and v == "deny" for k, v in roots.items()):
            msgs.append(f"FAIL {path}: permissions.{name} に .env の deny がありません (00 R2)")
```

`check_dir` の `for p in root.rglob("generation-profile.json"):` ブロックの直後に追加：

```python
    for p in root.rglob("config.toml"):
        if p.parent.name == ".codex":
            _check_codex_config(p, msgs)
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd generator && python3 -m unittest tests.test_selfcheck -v`
Expected: 全 PASS。

- [ ] **Step 5: コミット**

```bash
git add generator/agentsec/selfcheck.py generator/tests/test_selfcheck.py
git commit -m "feat: check codex config redlines in selfcheck"
```

---

## Task 2: selfcheck に Codex requirements 検査を追加（F4b）

**Files:**
- Modify: `generator/agentsec/selfcheck.py`
- Test: `generator/tests/test_selfcheck.py`

**Interfaces:**
- Consumes: Task 1 の `tomllib` import、`check_dir`。
- Produces: `_check_codex_requirements(path, msgs)` と補助 `_has_forbidden(prefix_rules, tokens) -> bool`。`check_dir` が `codex/requirements.toml` を検査する。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_selfcheck.py` の末尾に追記する。

```python
class TestCodexRequirements(unittest.TestCase):
    _CLEAN = (
        'allowed_approval_policies = ["untrusted", "on-request"]\n'
        'allowed_web_search_modes = ["cached"]\n'
        '[allowed_permission_profiles]\n'
        '":read-only" = true\n'
        'org-workspace = true\n'
        '[permissions.filesystem]\n'
        'deny_read = ["**/.env", "**/secrets/**", "~/.ssh", "~/.aws"]\n'
        '[rules]\n'
        'prefix_rules = [\n'
        '  { pattern = [{ token = "git" }, { token = "push" }], decision = "forbidden", justification = "x" },\n'
        '  { pattern = [{ token = "sudo" }], decision = "forbidden", justification = "y" },\n'
        ']\n'
    )

    def test_clean_requirements_passes(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/requirements.toml", self._CLEAN)
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)

    def test_danger_full_access_allowed_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/requirements.toml",
                   'allowed_web_search_modes = ["cached"]\n'
                   '[allowed_permission_profiles]\n'
                   '":danger-full-access" = true\n'
                   '[permissions.filesystem]\n'
                   'deny_read = ["**/.env", "~/.ssh"]\n'
                   '[rules]\n'
                   'prefix_rules = [\n'
                   '  { pattern = [{ token = "git" }, { token = "push" }], decision = "forbidden", justification = "x" },\n'
                   '  { pattern = [{ token = "sudo" }], decision = "forbidden", justification = "y" },\n'
                   ']\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("R3" in m for m in msgs))

    def test_missing_env_deny_read_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/requirements.toml",
                   self._CLEAN.replace('"**/.env", ', ""))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("R2" in m for m in msgs))

    def test_missing_git_push_forbidden_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/requirements.toml",
                   'allowed_web_search_modes = ["cached"]\n'
                   '[allowed_permission_profiles]\n'
                   'org-workspace = true\n'
                   '[permissions.filesystem]\n'
                   'deny_read = ["**/.env", "~/.ssh"]\n'
                   '[rules]\n'
                   'prefix_rules = [\n'
                   '  { pattern = [{ token = "sudo" }], decision = "forbidden", justification = "y" },\n'
                   ']\n')
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("R4" in m for m in msgs))

    def test_live_search_mode_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "codex/requirements.toml",
                   self._CLEAN.replace('["cached"]', '["cached", "live"]'))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("10.3.2" in m for m in msgs))
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `cd generator && python3 -m unittest tests.test_selfcheck -v`
Expected: `TestCodexRequirements` が FAIL（requirements.toml が未検査）。

- [ ] **Step 3: 実装する**

`generator/agentsec/selfcheck.py` の `_check_codex_config` の下に追加：

```python
def _has_forbidden(prefix_rules, tokens):
    for rule in prefix_rules:
        if not isinstance(rule, dict) or rule.get("decision") != "forbidden":
            continue
        pat = [t.get("token") for t in rule.get("pattern", [])
               if isinstance(t, dict) and "token" in t]
        if all(tok in pat for tok in tokens):
            return True
    return False


def _check_codex_requirements(path, msgs):
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("allowed_permission_profiles", {}).get(":danger-full-access"):
        msgs.append(f"FAIL {path}: allowed_permission_profiles に :danger-full-access (00 R3)")
    deny_read = data.get("permissions", {}).get("filesystem", {}).get("deny_read", [])
    if not any(".env" in d for d in deny_read):
        msgs.append(f"FAIL {path}: deny_read に .env がありません (00 R2)")
    if not any((".ssh" in d or ".aws" in d or ".kube" in d) for d in deny_read):
        msgs.append(f"FAIL {path}: deny_read に資格情報ディレクトリがありません (00 R2)")
    prefix_rules = data.get("rules", {}).get("prefix_rules", [])
    if not _has_forbidden(prefix_rules, ["git", "push"]):
        msgs.append(f"FAIL {path}: prefix_rules に git push の forbidden がありません (00 R4)")
    if not _has_forbidden(prefix_rules, ["sudo"]):
        msgs.append(f"FAIL {path}: prefix_rules に sudo の forbidden がありません (00 R4)")
    if "live" in data.get("allowed_web_search_modes", []):
        msgs.append(f"FAIL {path}: allowed_web_search_modes に live が含まれます (10.3.2)")
```

`check_dir` の Task 1 で追加した config.toml ループの直後に追加：

```python
    for p in root.rglob("requirements.toml"):
        _check_codex_requirements(p, msgs)
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd generator && python3 -m unittest tests.test_selfcheck -v`
Expected: 全 PASS。

- [ ] **Step 5: コミット**

```bash
git add generator/agentsec/selfcheck.py generator/tests/test_selfcheck.py
git commit -m "feat: check codex requirements redlines in selfcheck"
```

---

## Task 3: selfcheck に生成漏れ検出を追加（F5）

**Files:**
- Modify: `generator/agentsec/selfcheck.py`
- Test: `generator/tests/test_selfcheck.py`

**Interfaces:**
- Consumes: `check_dir`、`json`、`Path`。`generation-profile.json` の構造 `{"profile": {products, level, plan, use_container, ...}, "files": {...}, ...}`。
- Produces: `_expected_files(profile) -> list[str]` と `_check_completeness(root, msgs)`。`generation-profile.json` が存在するときだけ完全性を検査する。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_selfcheck.py` の末尾に追記する。

```python
def _profile_json(**profile):
    return json.dumps({"profile": profile})


class TestCompleteness(unittest.TestCase):
    def test_missing_managed_for_team_l3_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "generation-profile.json", _profile_json(
                products=["claude"], level="L3", plan="team", use_container=False))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("managed-settings.json" in m and "生成漏れ" in m for m in msgs))

    def test_missing_requirements_for_codex_team_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "generation-profile.json", _profile_json(
                products=["codex"], level="L2", plan="team", use_container=False))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("requirements.toml" in m and "生成漏れ" in m for m in msgs))

    def test_missing_dockerfile_when_container_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "generation-profile.json", _profile_json(
                products=["claude"], level="L2", plan="personal", use_container=True))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("Dockerfile" in m and "生成漏れ" in m for m in msgs))

    def test_no_profile_skips_completeness(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "claude-code/.claude/settings.json", json.dumps({
                "permissions": {"deny": ["Read(./.env)", "Bash(git push *)", "Bash(sudo *)"]},
                "sandbox": {"autoAllowBashIfSandboxed": False}}))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)

    def test_complete_personal_output_passes(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "claude-code/.claude/settings.json", json.dumps({
                "permissions": {"deny": ["Read(./.env)", "Bash(git push *)", "Bash(sudo *)"]},
                "sandbox": {"autoAllowBashIfSandboxed": False}}))
            for rel in ("acceptance/checklist.md", "acceptance/selfcheck.py",
                        "POLICY-SHEET.md", "README.md"):
                _write(d, rel, "x")
            _write(d, "generation-profile.json", _profile_json(
                products=["claude"], level="L2", plan="personal", use_container=False))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `cd generator && python3 -m unittest tests.test_selfcheck -v`
Expected: `test_missing_*` が FAIL（生成漏れを検出しないため code=0）。`test_no_profile_skips_completeness` と `test_complete_personal_output_passes` は現状でも PASS しうる。

- [ ] **Step 3: 実装する**

`generator/agentsec/selfcheck.py` の `_check_codex_requirements` の下に追加：

```python
def _expected_files(profile):
    products = profile.get("products", [])
    plan = profile.get("plan")
    level = profile.get("level")
    expected = ["acceptance/checklist.md", "acceptance/selfcheck.py",
                "POLICY-SHEET.md", "README.md", "generation-profile.json"]
    if "claude" in products:
        expected.append("claude-code/.claude/settings.json")
        if plan == "team" and level in ("L3", "L4"):
            expected.append("claude-code/managed-settings.json")
    if "codex" in products:
        expected.append("codex/.codex/config.toml")
        if plan == "team":
            expected.append("codex/requirements.toml")
    if profile.get("use_container"):
        expected += ["Dockerfile", "docker-compose.yml",
                     ".devcontainer/devcontainer.json", ".dockerignore"]
    return expected


def _check_completeness(root, msgs):
    prof_path = root / "generation-profile.json"
    if not prof_path.exists():
        return
    profile = json.loads(prof_path.read_text(encoding="utf-8")).get("profile", {})
    for rel in _expected_files(profile):
        if not (root / rel).exists():
            msgs.append(f"FAIL {root}: 生成漏れ — 期待ファイル '{rel}' がありません")
```

`check_dir` の最後、`code = 2 if ...` の直前に追加：

```python
    _check_completeness(root, msgs)
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd generator && python3 -m unittest tests.test_selfcheck -v`
Expected: 全 PASS。

- [ ] **Step 5: 既存 selfcheck テストの非回帰を確認**

Run: `cd generator && python3 -m unittest tests.test_selfcheck -v`
Expected: 既存 `TestSelfcheck`（clean/missing/compose/recorded）も全 PASS。`test_recorded_redline_still_fails` は profile キーを持たない `generation-profile.json` を書くが、`_check_completeness` は `profile={}` で always-files 欠落の FAIL を追加しても code=2 は不変・redline 断言も成立する（許容）。

- [ ] **Step 6: コミット**

```bash
git add generator/agentsec/selfcheck.py generator/tests/test_selfcheck.py
git commit -m "feat: detect generation gaps from profile in selfcheck"
```

---

## Task 4: build_codex の network 整理（F2）＋ web_search コメント（F3）

**Files:**
- Modify: `generator/agentsec/build_codex.py`
- Test: `generator/tests/test_build_codex.py`

**Interfaces:**
- Consumes: 既存 `build_config(level, stacks_keys, allowed_domains, extra_deny_paths)`、`build_requirements(level, allowed_domains, extra_deny_paths)`。
- Produces: 同シグネチャ・同出力（network セクションの値は不変）。

- [ ] **Step 1: 特性テスト（挙動固定）を書く**

`generator/tests/test_build_codex.py` の `TestBuildCodex` 内に追記する。これらは整理前後で常に PASS する回帰ガードである。

```python
    def test_config_network_with_domains(self):
        parsed = tomllib.loads(build_codex.build_config("L2", ["npm"], ["github.com"], []))
        net = parsed["permissions"]["business-workspace"]["network"]
        self.assertEqual(net, {"enabled": True, "domains": {"github.com": "allow"}})

    def test_config_network_without_domains(self):
        parsed = tomllib.loads(build_codex.build_config("L2", ["npm"], [], []))
        net = parsed["permissions"]["business-workspace"]["network"]
        self.assertEqual(net, {"enabled": False})

    def test_requirements_network_with_domains(self):
        parsed = tomllib.loads(build_codex.build_requirements("L2", ["github.com"], []))
        net = parsed["permissions"]["org-workspace"]["network"]
        self.assertEqual(net, {"enabled": True, "domains": {"github.com": "allow"}})

    def test_requirements_network_without_domains(self):
        parsed = tomllib.loads(build_codex.build_requirements("L2", [], []))
        net = parsed["permissions"]["org-workspace"]["network"]
        self.assertEqual(net, {"enabled": False})
```

- [ ] **Step 2: テストが通ることを確認（整理前のベースライン）**

Run: `cd generator && python3 -m unittest tests.test_build_codex -v`
Expected: 全 PASS（現行実装でも成立）。

- [ ] **Step 3: network 構築を1回代入へ整理する**

`generator/agentsec/build_codex.py` の `build_config` の L2+ 分岐を次へ置き換える。`network` を作り込んでから1回だけ代入し、末尾の再代入ブロックを削除する。

置換前（該当範囲）:

```python
    network = {"enabled": bool(allowed_domains)}
    config = {
        "approval_policy": "on-request",
        "web_search": prof["web_search"],
        "default_permissions": "business-workspace",
        "permissions": {
            "business-workspace": {
                "extends": ":workspace",
                "description": "Workspace editing with restricted network",
                "filesystem": {
                    ":root": "deny",
                    ":minimal": "read",
                    "glob_scan_max_depth": 4,
                    ":workspace_roots": workspace_roots,
                },
                "network": network,
            }
        },
    }
    if allowed_domains:
        config["permissions"]["business-workspace"]["network"] = {
            "enabled": True,
            "domains": {d: "allow" for d in allowed_domains},
        }
    return header + render_toml.dumps(config)
```

置換後:

```python
    network = {"enabled": bool(allowed_domains)}
    if allowed_domains:
        network["domains"] = {d: "allow" for d in allowed_domains}
    config = {
        "approval_policy": "on-request",
        "web_search": prof["web_search"],
        "default_permissions": "business-workspace",
        "permissions": {
            "business-workspace": {
                "extends": ":workspace",
                "description": "Workspace editing with restricted network",
                "filesystem": {
                    ":root": "deny",
                    ":minimal": "read",
                    "glob_scan_max_depth": 4,
                    ":workspace_roots": workspace_roots,
                },
                "network": network,
            }
        },
    }
    return header + render_toml.dumps(config)
```

`build_requirements` の `org-workspace` network も同様に整理する。`req` 辞書を作る前に network を組み、`org-workspace` 内で参照し、末尾の `if allowed_domains:` 再代入を削除する。

置換前（該当範囲）:

```python
    prof = rules.level_profile(level)
    req = {
        "allowed_approval_policies": ["untrusted", "on-request"],
        "allowed_web_search_modes": [prof["web_search"]] if prof["web_search"] != "disabled" else ["cached"],
```

置換後（network を先に組み、F3 コメントを付す）:

```python
    prof = rules.level_profile(level)
    org_network = {"enabled": bool(allowed_domains)}
    if allowed_domains:
        org_network["domains"] = {d: "allow" for d in allowed_domains}
    req = {
        "allowed_approval_policies": ["untrusted", "on-request"],
        # disabled は常に許可されるため、L4 の config(web_search=disabled) と
        # この allowed_web_search_modes(=["cached"]) は矛盾しない（docs 10.3.2/10.5）。
        "allowed_web_search_modes": [prof["web_search"]] if prof["web_search"] != "disabled" else ["cached"],
```

`org-workspace` 内の `"network": {"enabled": bool(allowed_domains)},` を `"network": org_network,` に変更し、関数末尾の

```python
    if allowed_domains:
        req["permissions"]["org-workspace"]["network"] = {
            "enabled": True, "domains": {d: "allow" for d in allowed_domains}}
    return "# 組織管理 requirements.toml（team プラン用）\n" + render_toml.dumps(req)
```

を

```python
    return "# 組織管理 requirements.toml（team プラン用）\n" + render_toml.dumps(req)
```

へ置き換える（再代入ブロックを削除）。

- [ ] **Step 4: テストが通ることを確認（挙動不変）**

Run: `cd generator && python3 -m unittest tests.test_build_codex -v`
Expected: 全 PASS（Step 1 の特性テスト含め、整理後も値が一致）。

- [ ] **Step 5: コミット**

```bash
git add generator/agentsec/build_codex.py generator/tests/test_build_codex.py
git commit -m "refactor: build codex network once and note web_search intent"
```

---

## Task 5: policy-sheet 連番化（F1）＋ placement_guide 追記

**Files:**
- Modify: `generator/templates/policy/policy-sheet.md.tmpl`
- Modify: `generator/agentsec/readme.py`
- Test: `generator/tests/test_readme.py`
- Test: `generator/tests/test_policy_sheet.py`（新規）

**Interfaces:**
- Consumes: `readme.placement_guide(file_keys) -> str`、`render_text.render(rel, mapping) -> str`。
- Produces: 連番化した policy-sheet テンプレ、モノレポ注記を含む placement_guide。

- [ ] **Step 1: policy-sheet 連番テストを書く（新規ファイル）**

`generator/tests/test_policy_sheet.py` を新規作成する。

```python
import unittest
from agentsec import render_text


class TestPolicySheet(unittest.TestCase):
    def _render(self):
        return render_text.render("policy/policy-sheet.md.tmpl", {
            "level": "L2", "plan": "team", "products": "claude, codex",
            "use_container": "True", "base_image": "node:20-bookworm-slim",
            "deny_paths": "./.env", "allowed_domains": "github.com",
            "deviations_block": "（なし）",
        })

    def test_sections_are_sequential(self):
        out = self._render()
        self.assertIn("## 4. ネットワーク", out)
        self.assertIn("## 5. 逸脱事項", out)
        self.assertNotIn("## 12.", out)
        self.assertNotIn("## 5. ネットワーク", out)
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `cd generator && python3 -m unittest tests.test_policy_sheet -v`
Expected: FAIL（現テンプレは `## 5. ネットワーク` / `## 12. 逸脱事項`）。

- [ ] **Step 3: テンプレを連番化する**

`generator/templates/policy/policy-sheet.md.tmpl` の見出し番号を 1〜5 の連番へ。`## 5. ネットワーク` を `## 4. ネットワーク` に、`## 12. 逸脱事項とリスク（リスク受容）` を `## 5. 逸脱事項とリスク（リスク受容）` に変更する（1/2/3 はそのまま）。

変更後の見出し:

```
## 1. 分類
## 2. 実行環境
## 3. ファイル / コマンド
## 4. ネットワーク
## 5. 逸脱事項とリスク（リスク受容）
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd generator && python3 -m unittest tests.test_policy_sheet -v`
Expected: PASS。

- [ ] **Step 5: placement_guide のモノレポ注記テストを書く**

`generator/tests/test_readme.py` の `TestPlacementGuide` に追記する。

```python
    def test_monorepo_note_present_for_local_layer(self):
        out = readme.placement_guide({"claude-code/.claude/settings.json"})
        self.assertIn("モノレポ", out)
        self.assertIn("共通", out)
```

- [ ] **Step 6: テストが失敗することを確認**

Run: `cd generator && python3 -m unittest tests.test_readme -v`
Expected: FAIL（注記がまだ無い）。

- [ ] **Step 7: placement_guide に注記を追加する**

`generator/agentsec/readme.py` の `placement_guide` の末尾、`lines += [...]` の最後の項目の後に1項目追加する。`has_local` が真のときだけ出るよう、`if has_local:` ブロックで `lines.append(...)` する。`return "\n".join(lines)` の直前に挿入:

```python
    if has_local:
        lines.append(
            "- モノレポ／複数プロジェクトを1コンテナにマウントする場合も、助言設定"
            "（`.claude/`・`.codex/`）は**ワークスペース/コンテナ共通の場所（例：コンテナ home の "
            "`~/.claude/`・`~/.codex/`）に1つ**置けば全サブプロジェクト・全マウントに効く"
            "（権限はメイン/サブ一律）。")
```

- [ ] **Step 8: テストが通ることを確認**

Run: `cd generator && python3 -m unittest tests.test_readme -v`
Expected: 全 PASS。

- [ ] **Step 9: コミット**

```bash
git add generator/templates/policy/policy-sheet.md.tmpl generator/agentsec/readme.py generator/tests/test_readme.py generator/tests/test_policy_sheet.py
git commit -m "docs: renumber policy sheet and note monorepo config placement"
```

---

## 最終検証（全タスク後）

- [ ] **全テスト**

Run: `cd generator && python3 -m unittest discover -s tests`
Expected: 全 PASS（既存 + 新規）。

- [ ] **生成→selfcheck スモーク（team・両製品・コンテナ）**

Run:
```bash
cd generator && python3 generate.py --profile profiles/examples/L2-team-both.json --output /tmp/gen-audit-smoke
python3 /tmp/gen-audit-smoke/acceptance/selfcheck.py /tmp/gen-audit-smoke
```
Expected: selfcheck が `PASS` を出力し exit 0（Codex 検査・完全性検査を含めて通過する）。
