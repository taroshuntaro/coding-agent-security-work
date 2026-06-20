# コーディングエージェント設定ジェネレータ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/` のセキュリティ・運用ガイドを、(レベル×プラン×製品×スタック) の入力から製品設定・コンテナ定義・受入テスト雛形・案件ポリシーシート・README へ変換する、Python 標準ライブラリのみの対話型生成スクリプトを実装する。

**Architecture:** 設定ファイル（JSON/TOML）は `agentsec/rules.py` のデータ構造から組み立て、`json.dumps` と自前の最小 TOML エミッタでシリアライズする。コンテナ定義・チェックリスト・ポリシーシート・README は外部 `.tmpl` を `string.Template` で穴埋めする。推奨外の値はレッドライン（原則拒否＋明示オーバーライド）と SHOULD 逸脱（記録して続行）に分類し、逸脱レジスタとして profile・ポリシーシート・README・selfcheck に追跡可能な形で残す。

**Tech Stack:** Python 3.11+（標準ライブラリのみ）、テストは標準 `unittest`、設計書 `docs/superpowers/specs/2026-06-21-agent-config-generator-design.md`。

## Global Constraints

- 実装・テストとも **Python 3 標準ライブラリのみ**。サードパーティ依存を追加しない（`pip install` 不要で動くこと）。
- TOML 書き込みは自前エミッタで行う（`tomllib` は読み取り専用、`tomli_w` は外部依存のため使わない）。
- Windows / Linux / macOS で同一コードが動くこと。パス操作は `pathlib`、改行は `\n` 固定（テンプレートは `newline=""` で書かない＝LF 統一）。
- レッドライン（00章 R1〜R6, MUST）違反の既定挙動は **原則拒否＋明示オーバーライド**。SHOULD 逸脱は記録して続行。
- 生成対象レベルは L1〜L4（L0 は対象外）。
- すべてのコミットメッセージは Conventional Commits（英語）。
- `agentsec/` パッケージはロジックのみ。対話 I/O は `generate.py` に閉じ込め、ロジック関数は引数で値を受け取る（テスト可能性のため）。

---

### Task 1: プロジェクト雛形と rules.py のデータモデル

**Files:**
- Create: `generator/agentsec/__init__.py`
- Create: `generator/agentsec/rules.py`
- Create: `generator/tests/__init__.py`
- Test: `generator/tests/test_rules.py`

**Interfaces:**
- Produces:
  - `LEVELS = ("L1", "L2", "L3", "L4")`, `PLANS = ("personal", "team")`, `PRODUCTS = ("claude", "codex")`
  - `BASE_DENY_COMMANDS: list[str]` — 全レベル共通で deny するコマンド断片（`curl *`, `wget *`, `ssh *`, `scp *`, `sudo *`, `kubectl *`, `helm *`, `terraform apply *`, `terraform destroy *`, `git push *`）
  - `SENSITIVE_READ_PATHS: list[str]` — `./.env`, `./.env.*`, `./secrets/**`, `./config/credentials.json`
  - `CREDENTIAL_DIRS: list[str]` — `~/.ssh`, `~/.aws`, `~/.kube`
  - `DEFAULT_ALLOWED_DOMAINS: list[str]` — `github.com`, `objects.githubusercontent.com`
  - `level_profile(level: str) -> dict` — レベルごとの方針フラグ（`{"default_mode": str, "managed_required": bool, "sandbox_fail_if_unavailable": bool, "web_search": str}`）

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_rules.py
import unittest
from agentsec import rules


class TestRules(unittest.TestCase):
    def test_constants_present(self):
        self.assertEqual(rules.LEVELS, ("L1", "L2", "L3", "L4"))
        self.assertIn("git push *", rules.BASE_DENY_COMMANDS)
        self.assertIn("sudo *", rules.BASE_DENY_COMMANDS)
        self.assertIn("./.env", rules.SENSITIVE_READ_PATHS)
        self.assertIn("~/.aws", rules.CREDENTIAL_DIRS)

    def test_level_profile_l1(self):
        p = rules.level_profile("L1")
        self.assertEqual(p["default_mode"], "plan")
        self.assertFalse(p["managed_required"])

    def test_level_profile_l3_requires_managed(self):
        p = rules.level_profile("L3")
        self.assertTrue(p["managed_required"])
        self.assertTrue(p["sandbox_fail_if_unavailable"])
        self.assertEqual(p["web_search"], "cached")

    def test_level_profile_invalid(self):
        with self.assertRaises(ValueError):
            rules.level_profile("L9")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_rules -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'agentsec'` または属性なし）

- [ ] **Step 3: Write minimal implementation**

```python
# generator/agentsec/__init__.py
# (空ファイル)
```

```python
# generator/agentsec/rules.py
"""レベル×プラン×製品ごとの設定ルールをデータとして定義する。

docs/00-red-lines.md, docs/10-codex.md, docs/11-claude-code.md の具体値に対応。
"""

LEVELS = ("L1", "L2", "L3", "L4")
PLANS = ("personal", "team")
PRODUCTS = ("claude", "codex")

BASE_DENY_COMMANDS = [
    "curl *", "wget *", "ssh *", "scp *", "sudo *",
    "kubectl *", "helm *", "terraform apply *", "terraform destroy *",
    "git push *",
]

SENSITIVE_READ_PATHS = [
    "./.env", "./.env.*", "./secrets/**", "./config/credentials.json",
]

CREDENTIAL_DIRS = ["~/.ssh", "~/.aws", "~/.kube"]

DEFAULT_ALLOWED_DOMAINS = ["github.com", "objects.githubusercontent.com"]

_LEVEL_PROFILES = {
    "L1": {"default_mode": "plan", "managed_required": False,
           "sandbox_fail_if_unavailable": False, "web_search": "cached"},
    "L2": {"default_mode": "default", "managed_required": False,
           "sandbox_fail_if_unavailable": False, "web_search": "cached"},
    "L3": {"default_mode": "default", "managed_required": True,
           "sandbox_fail_if_unavailable": True, "web_search": "cached"},
    "L4": {"default_mode": "default", "managed_required": True,
           "sandbox_fail_if_unavailable": True, "web_search": "disabled"},
}


def level_profile(level):
    if level not in _LEVEL_PROFILES:
        raise ValueError(f"unknown level: {level}")
    return dict(_LEVEL_PROFILES[level])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generator && python -m unittest tests.test_rules -v`
Expected: PASS（4 tests）

- [ ] **Step 5: Commit**

```bash
git add generator/agentsec/__init__.py generator/agentsec/rules.py generator/tests/__init__.py generator/tests/test_rules.py
git commit -m "feat: add rules data model for agent config generator"
```

---

### Task 2: stacks.py（ビルド/言語スタック → コマンド集合）

**Files:**
- Create: `generator/agentsec/stacks.py`
- Test: `generator/tests/test_stacks.py`

**Interfaces:**
- Consumes: なし
- Produces:
  - `STACKS: dict[str, dict]` — キーは `npm`/`maven`/`gradle`/`pip`/`dotnet`/`go`
  - `commands_for(stack_keys: list[str]) -> dict` — `{"allow": [...], "ask": [...]}` を統合して返す（重複排除・安定ソート）

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_stacks.py
import unittest
from agentsec import stacks


class TestStacks(unittest.TestCase):
    def test_npm_commands(self):
        result = stacks.commands_for(["npm"])
        self.assertIn("Bash(npm run test *)", result["allow"])
        self.assertIn("Bash(npm install *)", result["ask"])

    def test_multiple_stacks_merge_and_dedup(self):
        result = stacks.commands_for(["npm", "npm", "maven"])
        # 重複なし・ソート済み
        self.assertEqual(result["allow"], sorted(set(result["allow"])))
        self.assertTrue(any("mvn" in c for c in result["allow"]))

    def test_unknown_stack_raises(self):
        with self.assertRaises(ValueError):
            stacks.commands_for(["cobol"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_stacks -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: Write minimal implementation**

```python
# generator/agentsec/stacks.py
"""ビルド/言語スタックを allow/ask のコマンド集合へマッピングする。"""

STACKS = {
    "npm": {
        "allow": ["Bash(npm run lint)", "Bash(npm run test *)", "Bash(npm run build *)"],
        "ask": ["Bash(npm install *)"],
    },
    "maven": {
        "allow": ["Bash(mvn test *)", "Bash(mvn compile *)"],
        "ask": ["Bash(mvn install *)"],
    },
    "gradle": {
        "allow": ["Bash(gradle test *)", "Bash(gradle build *)"],
        "ask": ["Bash(gradle publish *)"],
    },
    "pip": {
        "allow": ["Bash(pytest *)", "Bash(python -m pytest *)"],
        "ask": ["Bash(pip install *)", "Bash(poetry install *)"],
    },
    "dotnet": {
        "allow": ["Bash(dotnet test *)", "Bash(dotnet build *)"],
        "ask": ["Bash(dotnet restore *)"],
    },
    "go": {
        "allow": ["Bash(go test *)", "Bash(go build *)"],
        "ask": ["Bash(go install *)"],
    },
}


def commands_for(stack_keys):
    allow, ask = set(), set()
    for key in stack_keys:
        if key not in STACKS:
            raise ValueError(f"unknown stack: {key}")
        allow.update(STACKS[key]["allow"])
        ask.update(STACKS[key]["ask"])
    return {"allow": sorted(allow), "ask": sorted(ask)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generator && python -m unittest tests.test_stacks -v`
Expected: PASS（3 tests）

- [ ] **Step 5: Commit**

```bash
git add generator/agentsec/stacks.py generator/tests/test_stacks.py
git commit -m "feat: add build stack to command mapping"
```

---

### Task 3: 最小 TOML エミッタ

**Files:**
- Create: `generator/agentsec/render_toml.py`
- Test: `generator/tests/test_render_toml.py`

**Interfaces:**
- Consumes: なし
- Produces:
  - `dumps(data: dict) -> str` — トップレベル key=value、`[section]`、`[section.sub]`、文字列/真偽/整数/文字列配列、配列内インラインテーブル（`[{token = "git"}, ...]`）に対応。dict は再帰的にセクション化、リスト要素が dict なら配列内インラインテーブルとして1行出力。

> 対応範囲は `docs/10-codex.md` の `config.toml`/`requirements.toml`（`prefix_rules` の `pattern`/`any_of` を含む）に限定する。汎用 TOML は目指さない。

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_render_toml.py
import unittest
from agentsec import render_toml as rt


class TestTomlEmitter(unittest.TestCase):
    def test_scalars(self):
        out = rt.dumps({"approval_policy": "on-request", "enabled": False, "depth": 4})
        self.assertIn('approval_policy = "on-request"', out)
        self.assertIn("enabled = false", out)
        self.assertIn("depth = 4", out)

    def test_string_array(self):
        out = rt.dumps({"allowed_web_search_modes": ["cached"]})
        self.assertIn('allowed_web_search_modes = ["cached"]', out)

    def test_section(self):
        out = rt.dumps({"permissions": {"org": {"description": "x"}}})
        self.assertIn("[permissions.org]", out)
        self.assertIn('description = "x"', out)

    def test_array_of_inline_tables(self):
        data = {"rules": {"prefix_rules": [
            {"pattern": [{"token": "git"}, {"token": "push"}],
             "decision": "forbidden"},
        ]}}
        out = rt.dumps(data)
        self.assertIn("[rules]", out)
        self.assertIn('pattern = [{token = "git"}, {token = "push"}]', out)
        self.assertIn('decision = "forbidden"', out)

    def test_roundtrip_parseable(self):
        import tomllib
        data = {"a": "b", "section": {"c": [1, 2], "d": True}}
        parsed = tomllib.loads(rt.dumps(data))
        self.assertEqual(parsed["a"], "b")
        self.assertEqual(parsed["section"]["c"], [1, 2])
        self.assertTrue(parsed["section"]["d"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_render_toml -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: Write minimal implementation**

```python
# generator/agentsec/render_toml.py
"""docs/10-codex.md の構造に限定した最小 TOML 書き込み。"""


def _fmt_scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise TypeError(f"unsupported scalar: {type(v)}")


def _fmt_inline_table(d):
    parts = []
    for k, v in d.items():
        if isinstance(v, list):
            parts.append(f"{k} = [{', '.join(_fmt_scalar(x) for x in v)}]")
        else:
            parts.append(f"{k} = {_fmt_scalar(v)}")
    return "{" + ", ".join(parts) + "}"


def _fmt_value(v):
    if isinstance(v, list):
        if v and all(isinstance(x, dict) for x in v):
            return "[" + ", ".join(_fmt_inline_table(x) for x in v) + "]"
        return "[" + ", ".join(_fmt_scalar(x) for x in v) + "]"
    return _fmt_scalar(v)


def _emit(data, prefix, lines):
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}
    if prefix and (scalars or not tables):
        lines.append(f"[{prefix}]")
    for k, v in scalars.items():
        lines.append(f"{k} = {_fmt_value(v)}")
    if scalars:
        lines.append("")
    for k, v in tables.items():
        new_prefix = f"{prefix}.{k}" if prefix else k
        _emit(v, new_prefix, lines)


def dumps(data):
    lines = []
    _emit(data, "", lines)
    return "\n".join(line for line in lines).rstrip("\n") + "\n"
```

> 注: 配列内インラインテーブルで `pattern` 内に `any_of` リストを持つケース（`{any_of = ["apply", "destroy"]}`）は `_fmt_inline_table` のリスト分岐で対応済み。Step 4 で `tomllib` ラウンドトリップが通ることを確認する。

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generator && python -m unittest tests.test_render_toml -v`
Expected: PASS（5 tests）

- [ ] **Step 5: Commit**

```bash
git add generator/agentsec/render_toml.py generator/tests/test_render_toml.py
git commit -m "feat: add minimal TOML emitter"
```

---

### Task 4: Codex 設定の組み立て（config.toml / requirements.toml）

**Files:**
- Create: `generator/agentsec/build_codex.py`
- Test: `generator/tests/test_build_codex.py`

**Interfaces:**
- Consumes: `rules`, `stacks.commands_for`, `render_toml.dumps`
- Produces:
  - `build_config(level, stacks_keys, allowed_domains, extra_deny_paths) -> str` — `~/.codex/config.toml` 文字列
  - `build_requirements(level, allowed_domains, extra_deny_paths) -> str` — 管理 `requirements.toml` 文字列（team プラン用）

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_build_codex.py
import unittest
import tomllib
from agentsec import build_codex


class TestBuildCodex(unittest.TestCase):
    def test_config_has_no_full_access_and_cached_search(self):
        toml = build_codex.build_config("L2", ["npm"], ["github.com"], [])
        parsed = tomllib.loads(toml)
        self.assertEqual(parsed["web_search"], "cached")
        self.assertEqual(parsed["approval_policy"], "on-request")

    def test_config_denies_sensitive_paths(self):
        toml = build_codex.build_config("L2", ["npm"], ["github.com"], ["**/keys/**"])
        self.assertIn("**/.env", toml)
        self.assertIn("**/keys/**", toml)

    def test_requirements_excludes_danger_full_access(self):
        toml = build_codex.build_requirements("L3", ["github.com"], [])
        parsed = tomllib.loads(toml)
        self.assertNotIn(":danger-full-access", parsed["allowed_permission_profiles"])
        self.assertEqual(parsed["allowed_web_search_modes"], ["cached"])

    def test_requirements_forbids_git_push(self):
        toml = build_codex.build_requirements("L3", ["github.com"], [])
        self.assertIn('decision = "forbidden"', toml)
        self.assertIn("git", toml)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_build_codex -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: Write minimal implementation**

```python
# generator/agentsec/build_codex.py
"""Codex の config.toml / requirements.toml を組み立てる。docs/10-codex.md 準拠。"""

from agentsec import rules, render_toml


def _filesystem_deny_paths(extra_deny_paths):
    base = ["**/.env", "**/.env.*", "**/secrets/**"]
    return base + list(extra_deny_paths)


def build_config(level, stacks_keys, allowed_domains, extra_deny_paths):
    prof = rules.level_profile(level)
    workspace_roots = {p: "deny" for p in _filesystem_deny_paths(extra_deny_paths)}
    workspace_roots[".devcontainer"] = "read"

    network = {"enabled": bool(allowed_domains)}
    config = {
        "approval_policy": "on-request",
        "web_search": prof["web_search"],
        "default_permissions": "business-workspace",
        "permissions": {
            "business-workspace": {
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
    header = "# ~/.codex/config.toml\n# extends = \":workspace\" を前提とする（適用時に確認）\n"
    return header + render_toml.dumps(config)


def build_requirements(level, allowed_domains, extra_deny_paths):
    prof = rules.level_profile(level)
    req = {
        "allowed_approval_policies": ["untrusted", "on-request"],
        "allowed_web_search_modes": [prof["web_search"]] if prof["web_search"] != "disabled" else ["cached"],
        "allow_remote_control": False,
        "allow_appshots": False,
        "allow_managed_hooks_only": True,
        "default_permissions": "org-workspace",
        "allowed_permission_profiles": {":read-only": True, "org-workspace": True},
        "permissions": {
            "filesystem": {
                "deny_read": _filesystem_deny_paths(extra_deny_paths) + rules.CREDENTIAL_DIRS,
            },
            "org-workspace": {
                "description": "Managed workspace access with sensitive files denied",
                "filesystem": {":root": "deny", ":minimal": "read", "glob_scan_max_depth": 4},
                "network": {"enabled": bool(allowed_domains)},
            },
        },
        "rules": {
            "prefix_rules": [
                {"pattern": [{"token": "git"}, {"token": "push"}], "decision": "forbidden",
                 "justification": "Remote repository mutation is performed outside the agent session."},
                {"pattern": [{"token": "sudo"}], "decision": "forbidden",
                 "justification": "Privilege escalation is not allowed."},
                {"pattern": [{"token": "terraform"}, {"any_of": ["apply", "destroy"]}], "decision": "forbidden",
                 "justification": "Infrastructure changes require an approved pipeline."},
            ]
        },
    }
    if allowed_domains:
        req["permissions"]["org-workspace"]["network"] = {
            "enabled": True, "domains": {d: "allow" for d in allowed_domains}}
    return "# 組織管理 requirements.toml（team プラン用）\n" + render_toml.dumps(req)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generator && python -m unittest tests.test_build_codex -v`
Expected: PASS（4 tests）

- [ ] **Step 5: Commit**

```bash
git add generator/agentsec/build_codex.py generator/tests/test_build_codex.py
git commit -m "feat: build codex config and requirements toml"
```

---

### Task 5: Claude Code 設定の組み立て（settings.json / managed-settings.json）

**Files:**
- Create: `generator/agentsec/build_claude.py`
- Test: `generator/tests/test_build_claude.py`

**Interfaces:**
- Consumes: `rules`, `stacks.commands_for`
- Produces:
  - `build_settings(level, stacks_keys, allowed_domains, extra_deny_paths) -> dict` — プロジェクト `settings.json` 相当の dict
  - `build_managed_settings(level, stacks_keys, allowed_domains, extra_deny_paths, denied_domains) -> dict` — `managed-settings.json` 相当の dict（team かつ L3+ 用）
  - いずれも呼び出し側で `json.dumps(..., indent=2, ensure_ascii=False)` する

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_build_claude.py
import unittest
from agentsec import build_claude


class TestBuildClaude(unittest.TestCase):
    def test_settings_denies_credentials_and_commands(self):
        s = build_claude.build_settings("L2", ["npm"], ["github.com"], [])
        self.assertIn("Read(./.env)", s["permissions"]["deny"])
        self.assertIn("Bash(git push *)", s["permissions"]["deny"])
        self.assertIn("~/.aws", s["sandbox"]["filesystem"]["denyRead"])

    def test_settings_allow_includes_stack_commands(self):
        s = build_claude.build_settings("L2", ["npm"], ["github.com"], [])
        self.assertIn("Bash(npm run test *)", s["permissions"]["allow"])

    def test_managed_disables_bypass_and_forces_sandbox(self):
        m = build_claude.build_managed_settings("L3", ["maven"], ["github.com"], [], [])
        self.assertEqual(m["permissions"]["disableBypassPermissionsMode"], "disable")
        self.assertTrue(m["sandbox"]["failIfUnavailable"])
        self.assertTrue(m["sandbox"]["filesystem"]["allowManagedReadPathsOnly"])
        self.assertTrue(m["allowManagedDomainsOnly"]
                        if "allowManagedDomainsOnly" in m
                        else m["sandbox"]["network"]["allowManagedDomainsOnly"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_build_claude -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: Write minimal implementation**

```python
# generator/agentsec/build_claude.py
"""Claude Code の settings.json / managed-settings.json を組み立てる。docs/11-claude-code.md 準拠。"""

from agentsec import rules, stacks

SCHEMA = "https://json.schemastore.org/claude-code-settings.json"


def _deny_reads(extra_deny_paths):
    return [f"Read({p})" for p in rules.SENSITIVE_READ_PATHS] + \
           [f"Read({p})" for p in extra_deny_paths]


def build_settings(level, stacks_keys, allowed_domains, extra_deny_paths):
    prof = rules.level_profile(level)
    cmds = stacks.commands_for(stacks_keys)
    return {
        "$schema": SCHEMA,
        "permissions": {
            "defaultMode": prof["default_mode"],
            "allow": cmds["allow"] + ["Bash(git status)", "Bash(git diff *)"],
            "ask": cmds["ask"] + ["Bash(git commit *)"],
            "deny": _deny_reads(extra_deny_paths)
                    + [f"Bash({c})" for c in rules.BASE_DENY_COMMANDS],
        },
        "sandbox": {
            "enabled": True,
            "autoAllowBashIfSandboxed": False,
            "allowUnsandboxedCommands": False,
            "filesystem": {"denyRead": list(rules.CREDENTIAL_DIRS)},
            "network": {"allowedDomains": list(allowed_domains)},
        },
    }


def build_managed_settings(level, stacks_keys, allowed_domains, extra_deny_paths, denied_domains):
    prof = rules.level_profile(level)
    cmds = stacks.commands_for(stacks_keys)
    return {
        "$schema": SCHEMA,
        "disableArtifact": True,
        "disableRemoteControl": True,
        "disableClaudeAiConnectors": True,
        "autoMemoryEnabled": False,
        "cleanupPeriodDays": 7,
        "permissions": {
            "defaultMode": prof["default_mode"],
            "disableBypassPermissionsMode": "disable",
            "disableAutoMode": "disable",
            "allow": ["Bash(git status)", "Bash(git diff *)"],
            "ask": cmds["ask"],
            "deny": _deny_reads(extra_deny_paths) + ["WebSearch"]
                    + [f"Bash({c})" for c in rules.BASE_DENY_COMMANDS],
        },
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": prof["sandbox_fail_if_unavailable"],
            "autoAllowBashIfSandboxed": False,
            "allowUnsandboxedCommands": False,
            "filesystem": {
                "denyRead": list(rules.CREDENTIAL_DIRS),
                "allowManagedReadPathsOnly": True,
            },
            "network": {
                "allowedDomains": list(allowed_domains),
                "deniedDomains": list(denied_domains),
                "allowManagedDomainsOnly": True,
            },
        },
        "allowedMcpServers": [],
        "allowManagedMcpServersOnly": True,
        "allowManagedPermissionRulesOnly": True,
        "allowManagedHooksOnly": True,
        "disableSkillShellExecution": True,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generator && python -m unittest tests.test_build_claude -v`
Expected: PASS（3 tests）

- [ ] **Step 5: Commit**

```bash
git add generator/agentsec/build_claude.py generator/tests/test_build_claude.py
git commit -m "feat: build claude code settings and managed-settings"
```

---

### Task 6: redlines.py（整合性チェックと逸脱分類）と deviation.py

**Files:**
- Create: `generator/agentsec/deviation.py`
- Create: `generator/agentsec/redlines.py`
- Test: `generator/tests/test_redlines.py`

**Interfaces:**
- Consumes: `rules`
- Produces:
  - `deviation.make(dtype, rule_ref, chosen, recommended, reason="", approver="", date="") -> dict` — 逸脱1件の dict（キー: `type,rule_ref,chosen,recommended,reason,approver,date`）。`dtype` は `"redline"` か `"recommendation"`
  - `redlines.check_inputs(level, plan, use_full_access, share_docker_socket, network_host, direct_push) -> list[dict]` — 入力から検出した逸脱（未記録）の list。L3/L4×personal、full access、docker socket、network host、direct push を `redline` として検出
  - `redlines.has_blocking(deviations, override=False) -> bool` — redline があり override 未指定なら True（=生成を止める）

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_redlines.py
import unittest
from agentsec import redlines, deviation


class TestRedlines(unittest.TestCase):
    def test_l3_personal_is_redline(self):
        devs = redlines.check_inputs("L3", "personal", False, False, False, False)
        refs = [d["rule_ref"] for d in devs]
        self.assertIn("00 R3/R6", refs)
        self.assertTrue(all(d["type"] == "redline" for d in devs))

    def test_full_access_is_redline(self):
        devs = redlines.check_inputs("L2", "team", True, False, False, False)
        self.assertTrue(any("R3" in d["rule_ref"] for d in devs))

    def test_clean_inputs_no_redline(self):
        devs = redlines.check_inputs("L2", "team", False, False, False, False)
        self.assertEqual(devs, [])

    def test_has_blocking(self):
        devs = redlines.check_inputs("L2", "team", True, False, False, False)
        self.assertTrue(redlines.has_blocking(devs, override=False))
        self.assertFalse(redlines.has_blocking(devs, override=True))

    def test_deviation_make(self):
        d = deviation.make("recommendation", "11.4", "wide domains", "narrow list",
                           reason="legacy CI", approver="alice", date="2026-06-21")
        self.assertEqual(d["type"], "recommendation")
        self.assertEqual(d["approver"], "alice")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_redlines -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: Write minimal implementation**

```python
# generator/agentsec/deviation.py
"""逸脱レジスタの1件を表すデータを生成する。"""


def make(dtype, rule_ref, chosen, recommended, reason="", approver="", date=""):
    if dtype not in ("redline", "recommendation"):
        raise ValueError(f"unknown deviation type: {dtype}")
    return {
        "type": dtype,
        "rule_ref": rule_ref,
        "chosen": chosen,
        "recommended": recommended,
        "reason": reason,
        "approver": approver,
        "date": date,
    }
```

```python
# generator/agentsec/redlines.py
"""docs/00-red-lines.md に基づく入力の整合性チェックと逸脱分類。"""

from agentsec import deviation


def check_inputs(level, plan, use_full_access, share_docker_socket,
                 network_host, direct_push):
    devs = []
    if level in ("L3", "L4") and plan == "personal":
        devs.append(deviation.make(
            "redline", "00 R3/R6",
            "L3/L4 on personal plan",
            "team plan with managed enforcement, or decline the engagement"))
    if use_full_access:
        devs.append(deviation.make(
            "redline", "00 R3",
            "bypass / danger-full-access as default",
            "regular permission mode without bypass"))
    if share_docker_socket:
        devs.append(deviation.make(
            "redline", "00 R3/09.2",
            "docker socket shared into container",
            "no docker socket mount"))
    if network_host:
        devs.append(deviation.make(
            "redline", "09.2",
            "--network host",
            "explicit egress allowlist"))
    if direct_push:
        devs.append(deviation.make(
            "redline", "00 R2/R4",
            "agent performs direct git push / deploy",
            "push and deploy via approved CI/CD only"))
    return devs


def has_blocking(deviations, override=False):
    if override:
        return False
    return any(d["type"] == "redline" for d in deviations)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generator && python -m unittest tests.test_redlines -v`
Expected: PASS（5 tests）

- [ ] **Step 5: Commit**

```bash
git add generator/agentsec/deviation.py generator/agentsec/redlines.py generator/tests/test_redlines.py
git commit -m "feat: add redline checks and deviation register"
```

---

### Task 7: profile.py（プロファイル読み書き・検証・記録メタ）

**Files:**
- Create: `generator/agentsec/profile.py`
- Test: `generator/tests/test_profile.py`

**Interfaces:**
- Consumes: なし（標準 `json`, `hashlib`, `datetime`, `pathlib`）
- Produces:
  - `REQUIRED_KEYS = ("products", "level", "plan", "stacks", "allowed_domains", "extra_deny_paths", "use_container")`
  - `validate(profile: dict) -> None` — 必須キー欠如や不正値で `ValueError`
  - `load(path: str) -> dict` / `save(path: str, profile: dict) -> None`
  - `file_sha256(path) -> str`
  - `build_record(profile, generated_files, deviations) -> dict` — `generation-profile.json` 用。`{"profile":..., "generated_at": ISO8601, "files": {relpath: sha256}, "deviations": [...]}`（製品バージョン欄は手記入用に `"product_versions": {}` を含める）

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_profile.py
import unittest
import tempfile
import os
import json
from agentsec import profile


class TestProfile(unittest.TestCase):
    def _valid(self):
        return {"products": ["claude"], "level": "L2", "plan": "team",
                "stacks": ["npm"], "allowed_domains": ["github.com"],
                "extra_deny_paths": [], "use_container": True}

    def test_validate_ok(self):
        profile.validate(self._valid())  # raises nothing

    def test_validate_missing_key(self):
        p = self._valid()
        del p["level"]
        with self.assertRaises(ValueError):
            profile.validate(p)

    def test_validate_bad_level(self):
        p = self._valid()
        p["level"] = "L9"
        with self.assertRaises(ValueError):
            profile.validate(p)

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "p.json")
            profile.save(path, self._valid())
            self.assertEqual(profile.load(path)["level"], "L2")

    def test_build_record_has_hashes_and_timestamp(self):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, "settings.json")
            with open(f, "w") as fh:
                fh.write("{}")
            rec = profile.build_record(self._valid(), {"settings.json": f}, [])
            self.assertIn("generated_at", rec)
            self.assertEqual(len(rec["files"]["settings.json"]), 64)  # sha256 hex
            self.assertIn("product_versions", rec)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_profile -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: Write minimal implementation**

```python
# generator/agentsec/profile.py
"""profile.json の読み書き・検証と generation-profile.json の記録メタ生成。"""

import json
import hashlib
from datetime import datetime, timezone

from agentsec import rules

REQUIRED_KEYS = ("products", "level", "plan", "stacks", "allowed_domains",
                 "extra_deny_paths", "use_container")


def validate(profile):
    for key in REQUIRED_KEYS:
        if key not in profile:
            raise ValueError(f"missing key: {key}")
    if profile["level"] not in rules.LEVELS:
        raise ValueError(f"invalid level: {profile['level']}")
    if profile["plan"] not in rules.PLANS:
        raise ValueError(f"invalid plan: {profile['plan']}")
    for p in profile["products"]:
        if p not in rules.PRODUCTS:
            raise ValueError(f"invalid product: {p}")


def load(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    validate(data)
    return data


def save(path, profile):
    validate(profile)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_record(profile, generated_files, deviations):
    return {
        "profile": profile,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_versions": {},  # 受入テスト時に手記入（docs/15-acceptance-tests.md 15.2）
        "files": {rel: file_sha256(path) for rel, path in generated_files.items()},
        "deviations": list(deviations),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generator && python -m unittest tests.test_profile -v`
Expected: PASS（5 tests）

- [ ] **Step 5: Commit**

```bash
git add generator/agentsec/profile.py generator/tests/test_profile.py
git commit -m "feat: add profile io, validation, and generation record"
```

---

### Task 8: selfcheck.py（生成物の静的レッドライン検査・3段階終了コード）

**Files:**
- Create: `generator/agentsec/selfcheck.py`
- Test: `generator/tests/test_selfcheck.py`

**Interfaces:**
- Consumes: 標準 `json`, `pathlib`
- Produces:
  - `check_dir(output_dir: str) -> tuple[int, list[str]]` — `(exit_code, messages)`。`exit_code` は 0(PASS/WARN) または 2(FAIL)
  - 検査: settings/managed の deny に `git push *`/`sudo *` 等、`.env` read deny、`sandbox.autoAllowBashIfSandboxed == False`、managed の `disableBypassPermissionsMode == "disable"`、`docker-compose.yml` に `privileged`/`network_mode: host`/`docker.sock`/`/:/host` がない。`generation-profile.json` の redline 逸脱は記録有無に関わらず FAIL を出す
  - `main()` — 同梱版が `python selfcheck.py [dir]` で動くエントリ（`sys.exit(code)`）

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_selfcheck.py
import unittest
import tempfile
import os
import json
from agentsec import selfcheck


def _write(d, rel, text):
    path = os.path.join(d, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class TestSelfcheck(unittest.TestCase):
    def test_clean_settings_pass(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "claude-code/.claude/settings.json", json.dumps({
                "permissions": {"deny": ["Read(./.env)", "Bash(git push *)", "Bash(sudo *)"]},
                "sandbox": {"autoAllowBashIfSandboxed": False},
            }))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0)

    def test_missing_git_push_deny_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "claude-code/.claude/settings.json", json.dumps({
                "permissions": {"deny": ["Read(./.env)"]},
                "sandbox": {"autoAllowBashIfSandboxed": False},
            }))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("git push" in m for m in msgs))

    def test_compose_docker_socket_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "docker-compose.yml",
                   "services:\n  dev:\n    volumes:\n      - /var/run/docker.sock:/var/run/docker.sock\n")
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("docker.sock" in m for m in msgs))

    def test_recorded_redline_still_fails(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "generation-profile.json", json.dumps({
                "deviations": [{"type": "redline", "rule_ref": "00 R3"}]}))
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 2)
            self.assertTrue(any("redline" in m.lower() for m in msgs))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_selfcheck -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: Write minimal implementation**

```python
# generator/agentsec/selfcheck.py
"""生成物のレッドライン静的検査。PASS/WARN=0, FAIL=2。

docs/15-acceptance-tests.md の注意: これは静的確認に過ぎない。
実拒否は受入テストで実環境・実バージョンに対して確認すること。
"""

import sys
import json
from pathlib import Path

REQUIRED_DENY = ["git push *", "sudo *"]
FORBIDDEN_COMPOSE = ["privileged", "network_mode: host", "docker.sock", "/:/host"]


def _check_claude_settings(path, msgs):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    deny = data.get("permissions", {}).get("deny", [])
    deny_text = " ".join(deny)
    for needle in REQUIRED_DENY:
        if needle not in deny_text:
            msgs.append(f"FAIL {path}: deny に '{needle}' がありません (00 R2/R4)")
    if not any(".env" in d for d in deny):
        msgs.append(f"FAIL {path}: .env の read deny がありません (00 R2)")
    sb = data.get("sandbox", {})
    if sb.get("autoAllowBashIfSandboxed", False):
        msgs.append(f"FAIL {path}: autoAllowBashIfSandboxed が true です (11.4)")


def _check_managed(path, msgs):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("permissions", {}).get("disableBypassPermissionsMode") != "disable":
        msgs.append(f"FAIL {path}: disableBypassPermissionsMode != disable (00 R3)")


def _check_compose(path, msgs):
    text = Path(path).read_text(encoding="utf-8")
    for needle in FORBIDDEN_COMPOSE:
        if needle in text:
            msgs.append(f"FAIL {path}: '{needle}' を検出 (09.2)")


def _check_profile(path, msgs):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for dev in data.get("deviations", []):
        if dev.get("type") == "redline":
            msgs.append(f"FAIL {path}: 記録済みだが redline 逸脱あり ({dev.get('rule_ref')})")
        elif dev.get("type") == "recommendation":
            msgs.append(f"WARN {path}: SHOULD 逸脱 ({dev.get('rule_ref')})")


def check_dir(output_dir):
    root = Path(output_dir)
    msgs = []
    for p in root.rglob("settings.json"):
        if "managed" not in p.name:
            _check_claude_settings(p, msgs)
    for p in root.rglob("managed-settings.json"):
        _check_managed(p, msgs)
    for p in root.rglob("docker-compose.yml"):
        _check_compose(p, msgs)
    for p in root.rglob("generation-profile.json"):
        _check_profile(p, msgs)
    code = 2 if any(m.startswith("FAIL") for m in msgs) else 0
    return code, msgs


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    code, msgs = check_dir(target)
    for m in msgs:
        print(m)
    print("PASS" if code == 0 and not msgs else ("WARN" if code == 0 else "FAIL"))
    sys.exit(code)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generator && python -m unittest tests.test_selfcheck -v`
Expected: PASS（4 tests）

- [ ] **Step 5: Commit**

```bash
git add generator/agentsec/selfcheck.py generator/tests/test_selfcheck.py
git commit -m "feat: add static redline selfcheck with tri-state exit"
```

---

### Task 9: テキストテンプレートと render_text.py

**Files:**
- Create: `generator/agentsec/render_text.py`
- Create: `generator/templates/container/Dockerfile.tmpl`
- Create: `generator/templates/container/docker-compose.yml.tmpl`
- Create: `generator/templates/container/devcontainer.json.tmpl`
- Create: `generator/templates/container/dockerignore.tmpl`
- Create: `generator/templates/acceptance/checklist.md.tmpl`
- Create: `generator/templates/policy/policy-sheet.md.tmpl`
- Create: `generator/templates/policy/README.md.tmpl`
- Test: `generator/tests/test_render_text.py`

**Interfaces:**
- Consumes: 標準 `string.Template`, `pathlib`
- Produces:
  - `render(template_name: str, mapping: dict) -> str` — `templates/` 配下の `.tmpl` を `string.Template().substitute` で穴埋め（不足キーは `KeyError`）
  - `render` は `templates/` をパッケージ相対で解決する

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_render_text.py
import unittest
from agentsec import render_text


class TestRenderText(unittest.TestCase):
    def test_dockerfile_renders_nonroot(self):
        out = render_text.render("container/Dockerfile.tmpl",
                                 {"base_image": "node:20-bookworm-slim"})
        self.assertIn("node:20-bookworm-slim", out)
        self.assertIn("USER", out)

    def test_compose_has_security_opts(self):
        out = render_text.render("container/docker-compose.yml.tmpl",
                                 {"service_name": "dev"})
        self.assertIn("no-new-privileges", out)
        self.assertIn("read_only", out)

    def test_missing_key_raises(self):
        with self.assertRaises(KeyError):
            render_text.render("container/Dockerfile.tmpl", {})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_render_text -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: Write implementation and templates**

```python
# generator/agentsec/render_text.py
"""templates/ 配下の .tmpl を string.Template で穴埋めする。"""

from pathlib import Path
from string import Template

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def render(template_name, mapping):
    text = (_TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    return Template(text).substitute(mapping)
```

`generator/templates/container/Dockerfile.tmpl`（docs/09-containers.md 9.1 準拠。非root・最小権限）:

```dockerfile
# docs/09-containers.md 9.1 に準拠。ベースイメージは digest 固定を推奨。
FROM $base_image

# 非rootユーザー
RUN useradd --create-home --shell /bin/bash agent || true
WORKDIR /workspace

# 必要ツールのみを固定バージョンで導入する（例: ここに追記）
# RUN ...

USER agent
# bind mount された /workspace のみを編集対象とする
```

`generator/templates/container/docker-compose.yml.tmpl`（9.1/9.2 準拠）:

```yaml
# docs/09-containers.md 準拠。privileged / network host / docker.sock は使用しない。
services:
  $service_name:
    build: .
    user: agent
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    pids_limit: 512
    mem_limit: 2g
    cpus: 2.0
    volumes:
      # 対象リポジトリだけをマウント（read-only を優先、編集が必要なら rw）
      - ./:/workspace:rw
    # エグレスは必要ドメインのみ。ホストネットワークは使わない。
```

`generator/templates/container/devcontainer.json.tmpl`:

```json
{
  "name": "$service_name-agent",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "$service_name",
  "workspaceFolder": "/workspace",
  "remoteUser": "agent",
  "overrideCommand": false
}
```

`generator/templates/container/dockerignore.tmpl`:

```text
.env
.env.*
secrets/
**/credentials.json
.git
node_modules
```

`generator/templates/acceptance/checklist.md.tmpl`（docs/15-acceptance-tests.md 15.1 のマトリクス）:

```markdown
# 受入テスト チェックリスト（レベル $level / プラン $plan）

> docs/15-acceptance-tests.md 準拠。ダミー値・隔離環境で「実際に拒否される」ことを確認する。
> selfcheck.py は静的確認に過ぎない。下表は実環境・実バージョンで実施する。

| テスト | 期待結果 | 結果 |
|---|---|---|
| ワークスペース内の通常ファイルを読む | 許可 | |
| .env / secrets / ホスト資格情報を読む | 拒否 | |
| ワークスペース外へ書き込む | 拒否または承認 | |
| curl 等で未許可ドメインへ通信 | 拒否 | |
| git push / terraform apply / kubectl 変更 | 拒否または独立承認 | |
| 未承認 MCP / Hooks / Plugins を追加 | 無効化または拒否 | |
| bypass / full access を起動・選択 | 拒否または管理的に不可 | |
| sandbox 依存が欠けた状態で起動 | 機密レベルでは起動失敗 | |
| コンテナ内からホストのホーム / docker socket | 拒否 | |
| セッション終了・環境破棄後 | シークレット・履歴が残らない | |

## 記録（15.2）
- 実施日 / 実施者:
- 製品バージョン / OS:
- 設定ファイルハッシュ: generation-profile.json を参照
```

`generator/templates/policy/policy-sheet.md.tmpl`（docs/appendix-a-policy-template.md ベース。逸脱欄を強調）:

```markdown
# コーディングエージェント利用ポリシー: <案件名>

## 1. 分類
- 利用レベル: $level
- 契約プラン: $plan
- 利用可能製品: $products

## 2. 実行環境
- コンテナ利用: $use_container
- ベースイメージ: $base_image

## 3. ファイル / コマンド
- deny 対象パス: $deny_paths
- deny コマンド: docs/00 R2/R4 準拠（git push, sudo, curl 等）

## 5. ネットワーク
- 許可ドメイン: $allowed_domains

## 12. 逸脱事項とリスク（リスク受容）
$deviations_block

> レッドライン逸脱がある場合、本案件は docs/00-red-lines.md 上「業務利用と認めない」状態である。
> 続行には組織の例外承認が必要。
```

`generator/templates/policy/README.md.tmpl`:

```markdown
# 生成された設定の適用手順

- 対象レベル: $level / プラン: $plan / 製品: $products

## 適用
- Claude Code プロジェクト設定: `claude-code/.claude/settings.json` をリポジトリへ
- Claude Code 管理設定（team/L3+）: `claude-code/managed-settings.json` をリポジトリ外の管理パスへ
- Codex: `codex/.codex/config.toml`、管理は `codex/requirements.toml`
- コンテナ: `Dockerfile` / `docker-compose.yml` / `.devcontainer/`

## 検証（必須）
1. `python acceptance/selfcheck.py .` で静的検査（PASS を確認）
2. `acceptance/checklist.md` を実環境で実施し「実拒否」を確認（docs/00 R5）

## 逸脱事項
$deviations_block
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd generator && python -m unittest tests.test_render_text -v`
Expected: PASS（3 tests）

- [ ] **Step 5: Commit**

```bash
git add generator/agentsec/render_text.py generator/templates generator/tests/test_render_text.py
git commit -m "feat: add text templates and renderer"
```

---

### Task 10: generate.py（対話・プロファイル再生・オーバーライド・結線）とゴールデン

**Files:**
- Create: `generator/generate.py`
- Create: `generator/agentsec/orchestrate.py`
- Create: `generator/README.md`
- Create: `generator/profiles/examples/L2-team-both.json`
- Test: `generator/tests/test_orchestrate.py`

**Interfaces:**
- Consumes: 全 `agentsec` モジュール
- Produces:
  - `orchestrate.generate(profile: dict, output_dir: str, deviations: list, base_image: str) -> dict` — 全成果物をディスクへ書き出し、`generation-profile.json` を含む `{relpath: abspath}` を返す
  - `generate.py`：`--profile PATH`（非対話再生）、`--output DIR`、`--allow-redline-override`、`--approver NAME` を持つ CLI。プロファイル無指定なら対話収集

- [ ] **Step 1: Write the failing test**

```python
# generator/tests/test_orchestrate.py
import unittest
import tempfile
import os
import json
from agentsec import orchestrate, selfcheck


class TestOrchestrate(unittest.TestCase):
    def _profile(self):
        return {"products": ["claude", "codex"], "level": "L2", "plan": "team",
                "stacks": ["npm"], "allowed_domains": ["github.com"],
                "extra_deny_paths": [], "use_container": True}

    def test_generates_expected_files(self):
        with tempfile.TemporaryDirectory() as d:
            files = orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            self.assertIn("claude-code/.claude/settings.json", files)
            self.assertIn("claude-code/managed-settings.json", files)
            self.assertIn("codex/.codex/config.toml", files)
            self.assertIn("docker-compose.yml", files)
            self.assertIn("generation-profile.json", files)
            self.assertTrue(os.path.exists(files["generation-profile.json"]))

    def test_generated_output_passes_selfcheck(self):
        with tempfile.TemporaryDirectory() as d:
            orchestrate.generate(self._profile(), d, [], "node:20-bookworm-slim")
            code, msgs = selfcheck.check_dir(d)
            self.assertEqual(code, 0, msgs)

    def test_personal_plan_skips_managed(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._profile()
            p["plan"] = "personal"
            p["level"] = "L2"
            files = orchestrate.generate(p, d, [], "node:20-bookworm-slim")
            self.assertNotIn("claude-code/managed-settings.json", files)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd generator && python -m unittest tests.test_orchestrate -v`
Expected: FAIL（ModuleNotFoundError）

- [ ] **Step 3: Write minimal implementation**

```python
# generator/agentsec/orchestrate.py
"""入力プロファイルから全成果物を書き出す。"""

import json
from pathlib import Path

from agentsec import (rules, build_claude, build_codex, render_text,
                      profile as profile_mod)


def _write(out_root, rel, text):
    path = Path(out_root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return str(path)


def _json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _deviations_block(deviations):
    if not deviations:
        return "（なし）"
    return "\n".join(
        f"- [{d['type']}] {d['rule_ref']}: {d['chosen']} "
        f"（推奨: {d['recommended']} / 理由: {d['reason']} / 承認: {d['approver']}）"
        for d in deviations)


def generate(profile, output_dir, deviations, base_image):
    profile_mod.validate(profile)
    files = {}
    lvl, plan = profile["level"], profile["plan"]
    domains = profile["allowed_domains"]
    extra = profile["extra_deny_paths"]
    stacks_keys = profile["stacks"]

    if "claude" in profile["products"]:
        files["claude-code/.claude/settings.json"] = _write(
            output_dir, "claude-code/.claude/settings.json",
            _json(build_claude.build_settings(lvl, stacks_keys, domains, extra)))
        if plan == "team" and lvl in ("L3", "L4"):
            files["claude-code/managed-settings.json"] = _write(
                output_dir, "claude-code/managed-settings.json",
                _json(build_claude.build_managed_settings(lvl, stacks_keys, domains, extra, [])))

    if "codex" in profile["products"]:
        files["codex/.codex/config.toml"] = _write(
            output_dir, "codex/.codex/config.toml",
            build_codex.build_config(lvl, stacks_keys, domains, extra))
        if plan == "team":
            files["codex/requirements.toml"] = _write(
                output_dir, "codex/requirements.toml",
                build_codex.build_requirements(lvl, domains, extra))

    if profile["use_container"]:
        files["Dockerfile"] = _write(output_dir, "Dockerfile",
            render_text.render("container/Dockerfile.tmpl", {"base_image": base_image}))
        files["docker-compose.yml"] = _write(output_dir, "docker-compose.yml",
            render_text.render("container/docker-compose.yml.tmpl", {"service_name": "dev"}))
        files[".devcontainer/devcontainer.json"] = _write(output_dir, ".devcontainer/devcontainer.json",
            render_text.render("container/devcontainer.json.tmpl", {"service_name": "dev"}))
        files[".dockerignore"] = _write(output_dir, ".dockerignore",
            render_text.render("container/dockerignore.tmpl", {}))

    text_map = {
        "level": lvl, "plan": plan, "products": ", ".join(profile["products"]),
        "use_container": str(profile["use_container"]), "base_image": base_image,
        "deny_paths": ", ".join(rules.SENSITIVE_READ_PATHS + extra),
        "allowed_domains": ", ".join(domains),
        "deviations_block": _deviations_block(deviations),
    }
    files["acceptance/checklist.md"] = _write(output_dir, "acceptance/checklist.md",
        render_text.render("acceptance/checklist.md.tmpl", text_map))
    files["POLICY-SHEET.md"] = _write(output_dir, "POLICY-SHEET.md",
        render_text.render("policy/policy-sheet.md.tmpl", text_map))
    files["README.md"] = _write(output_dir, "README.md",
        render_text.render("policy/README.md.tmpl", text_map))

    # selfcheck.py を生成物へ同梱（パッケージから読み出してコピー）
    selfcheck_src = (Path(__file__).resolve().parent / "selfcheck.py").read_text(encoding="utf-8")
    files["acceptance/selfcheck.py"] = _write(output_dir, "acceptance/selfcheck.py", selfcheck_src)

    record = profile_mod.build_record(profile, files, deviations)
    files["generation-profile.json"] = _write(output_dir, "generation-profile.json", _json(record))
    return files
```

> 同梱版 `selfcheck.py` は `from agentsec import ...` を持たないため、そのままコピーで動く（Task 8 の実装は標準ライブラリのみ依存）。

```python
# generator/generate.py
"""対話 / --profile 再生で設定一式を生成する CLI。"""

import argparse
import sys

from agentsec import rules, redlines, orchestrate, profile as profile_mod


def _ask(prompt, choices=None):
    while True:
        ans = input(prompt).strip()
        if not choices or ans in choices:
            return ans
        print(f"  選択肢: {', '.join(choices)}")


def _collect_interactive():
    products = []
    if _ask("Claude Code を含める? (y/n): ", ["y", "n"]) == "y":
        products.append("claude")
    if _ask("Codex を含める? (y/n): ", ["y", "n"]) == "y":
        products.append("codex")
    level = _ask(f"レベル {rules.LEVELS}: ", list(rules.LEVELS))
    plan = _ask("プラン (personal/team): ", list(rules.PLANS))
    stacks = _ask("スタック (カンマ区切り 例 npm,maven): ").split(",")
    stacks = [s.strip() for s in stacks if s.strip()]
    domains = _ask("許可ドメイン (カンマ区切り): ").split(",")
    domains = [d.strip() for d in domains if d.strip()] or list(rules.DEFAULT_ALLOWED_DOMAINS)
    extra = _ask("追加 deny パス (カンマ区切り、なければ空): ").split(",")
    extra = [e.strip() for e in extra if e.strip()]
    use_container = _ask("コンテナ定義を出力? (y/n): ", ["y", "n"]) == "y"
    return {"products": products, "level": level, "plan": plan, "stacks": stacks,
            "allowed_domains": domains, "extra_deny_paths": extra,
            "use_container": use_container}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile")
    parser.add_argument("--output", default="./generated")
    parser.add_argument("--base-image", default="node:20-bookworm-slim")
    parser.add_argument("--allow-redline-override", action="store_true")
    parser.add_argument("--approver", default="")
    args = parser.parse_args(argv)

    if args.profile:
        profile = profile_mod.load(args.profile)
    else:
        profile = _collect_interactive()

    devs = redlines.check_inputs(
        profile["level"], profile["plan"],
        use_full_access=False, share_docker_socket=False,
        network_host=False, direct_push=False)
    if redlines.has_blocking(devs, override=args.allow_redline_override):
        print("レッドライン違反のため生成を中止します:")
        for d in devs:
            print(f"  - {d['rule_ref']}: {d['chosen']} (推奨: {d['recommended']})")
        print("続行するには --allow-redline-override と --approver を指定してください。")
        return 2
    for d in devs:
        d["approver"] = args.approver
        d["date"] = __import__("datetime").date.today().isoformat()

    files = orchestrate.generate(profile, args.output, devs, args.base_image)
    print(f"{len(files)} 件を {args.output} に生成しました。")
    print("検証: python acceptance/selfcheck.py", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`generator/profiles/examples/L2-team-both.json`:

```json
{
  "products": ["claude", "codex"],
  "level": "L2",
  "plan": "team",
  "stacks": ["npm"],
  "allowed_domains": ["github.com", "objects.githubusercontent.com"],
  "extra_deny_paths": [],
  "use_container": true
}
```

`generator/README.md`:

```markdown
# コーディングエージェント設定ジェネレータ

`docs/` のセキュリティ・運用ガイドから、製品設定・コンテナ定義・受入テスト雛形・
ポリシーシートを生成する。Python 3.11+ 標準ライブラリのみ。

## 使い方
- 対話: `python generate.py --output ./generated`
- 再生: `python generate.py --profile profiles/examples/L2-team-both.json --output ./generated`
- 検証: `python generated/acceptance/selfcheck.py ./generated`

## テスト
`cd generator && python -m unittest discover -s tests`

## 注意
selfcheck は静的確認に過ぎない。実拒否は docs/15-acceptance-tests.md の受入テストで確認する。
レッドライン違反（docs/00）は既定で生成拒否。続行には --allow-redline-override と --approver。
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd generator && python -m unittest discover -s tests -v`
Expected: PASS（全タスクのテスト合計）

- [ ] **Step 5: Commit**

```bash
git add generator/generate.py generator/agentsec/orchestrate.py generator/README.md generator/profiles generator/tests/test_orchestrate.py
git commit -m "feat: wire up interactive generator and orchestration"
```

---

## Self-Review

**Spec coverage（設計書の各節）:**
- §3.1 設定=データ駆動 → Task 1,3,4,5。§3.2 テキスト=テンプレート → Task 9。§3.3 ディレクトリ構成 → Task 1〜10 で対応。
- §4 入力軸 → Task 10 `_collect_interactive`（製品/レベル/プラン/スタック/ドメイン/deny/コンテナ/出力先）。
- §5 推奨外の扱い（redline/recommendation 分類、対話提示、3記録先） → Task 6（分類）、Task 10（オーバーライド・記録）、Task 9（policy-sheet/README の逸脱欄）、Task 7（profile への記録）。
- §6 出力物 → Task 10 `orchestrate.generate`（個人系で managed/requirements を出さない条件含む）。
- §7 selfcheck 3段階 → Task 8。
- §8 エラーハンドリング → Task 6（不正組合せ）、Task 7（profile 検証）。`--force` 上書き確認は Task 10 の CLI で追加実装（既存ファイル検出時に確認）。
- §9 テスト方針 → 各 Task の unittest、Task 8 の負のテスト、Task 10 のゴールデン相当（selfcheck 通過確認）。

**Placeholder scan:** 各ステップに実コード/実テンプレートを記載済み。"TBD"/"後で" なし。

**Type consistency:** `build_settings`/`build_managed_settings`（dict 返し）、`build_config`/`build_requirements`（str 返し）、`commands_for`→`{"allow","ask"}`、`check_inputs`→list[dict]、`generate`→dict[relpath,abspath] が各 Task 間で一致。`level_profile` のキー（`default_mode`/`managed_required`/`sandbox_fail_if_unavailable`/`web_search`）も Task 1 定義と Task 4,5 利用で一致。

**補足:** `--force`（既存出力の上書き確認）は Task 10 の CLI に、対話中の SHOULD 逸脱その場記録は Task 10 拡張として実装する。コア（redline ブロッキング・記録）は計画済みで、追加は小さな分岐に閉じる。
