# Generator UX フェーズ2: スタック自動検出 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 対象プロジェクトのマーカーファイルからビルド/言語スタックを自動検出し、対話で提示・確認できるようにして、ユーザーが手動でスタックを列挙する負担（当初課題3）を解消する。あわせて単一スタック検出時に base-image を推定し（改善12）、生成物に設定の配置3層・優先順位・R6 注記（プロジェクト設定は強制ではない）を明示する（配置スコープ明確化の最小版）。

**Architecture:** 検出ロジックは純関数 `agentsec/detect.py`（ファイルシステム読み取りのみ、対話 I/O なし）に置き、対話での提示・確認・手動フォールバックは `generate.py` に閉じ込める（既存方針どおり）。検出は対象配下を深さ制限付きで再帰走査し、依存/VCS/成果物ディレクトリを枝刈りした上で検出スタックの **union** を返す（モノレポ・複数プロジェクトのマウントに対応；生成設定はコンテナ単位で1つのため union が正しい）。スタックの追加は `STACKS`/`MARKERS`/`BASE_IMAGES` へのデータ追記だけで済み、ドリフトは整合テストで防ぐ。検出結果の stacks は従来どおり `profile["stacks"]` に入り、推定/指定した base-image は新たに `profile["base_image"]`（任意キー）に保存する。`--profile` 再生時は検出を行わず profile の値を優先する。

**Tech Stack:** Python 3.11+ 標準ライブラリのみ（`pathlib`、`unittest`）。

## Global Constraints

- Python 3.11 以上、標準ライブラリのみ。サードパーティ依存を追加しない（`pip install` なしで動く）。
- `agentsec/` はロジックのみ。対話 I/O（input/print）は `generate.py` に閉じ込める。`agentsec/` の関数は引数で値を受け取りテスト可能にする。
- `agentsec/selfcheck.py` は standalone を保つ（`from agentsec import ...` を入れない）。本プランは selfcheck.py を変更しない。
- テストは標準 `unittest`。実行: `cd generator && python3 -m unittest discover -s tests`。
- 改行は LF。パス操作は `pathlib`、ファイル I/O は `encoding="utf-8"`。
- TDD（失敗するテスト → 実装 → 通過）。コミットは英語 Conventional Commits（subject は命令形・小文字始まり・末尾ピリオドなし、おおむね50文字以内）。
- `--profile` 再生時は profile の `stacks` を優先し、検出は対話時のみ行う（既存の不変条件）。
- レッドライン/承認まわりの既存フロー（`main` の exit-2 等）は変更しない。

---

### Task 1: detect.py — マーカーファイルからのスタック検出

**Files:**
- Create: `generator/agentsec/detect.py`
- Test: `generator/tests/test_detect.py`

**Interfaces:**
- Produces:
  - `detect.MARKERS: dict[str, str]` — マーカーファイル名/グロブ → 既知スタックキー（`stacks.KNOWN` の部分集合）。
  - `detect.UNSUPPORTED_MARKERS: dict[str, str]` — マーカー → 未対応スタック名（警告用ラベル）。
  - `detect.IGNORE_DIRS: set[str]` — 走査時に降りない依存/VCS/成果物ディレクトリ名。
  - `detect.MAX_DEPTH: int` — 既定の走査深さ（3）。
  - `detect.detect_stacks(target_dir, max_depth=MAX_DEPTH) -> dict` — `target_dir` 配下を `max_depth` まで再帰走査し、`IGNORE_DIRS`・隠しディレクトリを枝刈りして検出スタックの **union** を `{"known": [...], "unsupported": [...]}`（ソート済み・重複なし）で返す。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_detect.py` を新規作成:

```python
import unittest
import tempfile
from pathlib import Path
from agentsec import detect, stacks


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestDetectStacks(unittest.TestCase):
    def test_detects_markers_in_root(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "package.json")
            _touch(Path(d) / "go.mod")
            result = detect.detect_stacks(d)
            self.assertEqual(result["known"], ["go", "npm"])
            self.assertEqual(result["unsupported"], [])

    def test_csproj_glob_detects_dotnet(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "App.csproj")
            self.assertEqual(detect.detect_stacks(d)["known"], ["dotnet"])

    def test_pip_markers_dedup_to_single_key(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "pyproject.toml")
            _touch(Path(d) / "requirements.txt")
            self.assertEqual(detect.detect_stacks(d)["known"], ["pip"])

    def test_unions_across_subprojects(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "proj-a" / "package.json")
            _touch(Path(d) / "proj-b" / "go.mod")
            self.assertEqual(detect.detect_stacks(d)["known"], ["go", "npm"])

    def test_monorepo_nested_packages(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "packages" / "web" / "package.json")
            _touch(Path(d) / "services" / "api" / "go.mod")
            self.assertEqual(detect.detect_stacks(d)["known"], ["go", "npm"])

    def test_ignores_dependency_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "go.mod")
            _touch(Path(d) / "node_modules" / "dep" / "package.json")
            # node_modules は枝刈りされ npm を拾わない
            self.assertEqual(detect.detect_stacks(d)["known"], ["go"])

    def test_respects_max_depth(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "a" / "b" / "c" / "d" / "package.json")
            # max_depth=2 では深すぎて拾わない
            self.assertEqual(detect.detect_stacks(d, max_depth=2)["known"], [])

    def test_unsupported_markers_reported(self):
        with tempfile.TemporaryDirectory() as d:
            _touch(Path(d) / "Cargo.toml")
            _touch(Path(d) / "Gemfile")
            result = detect.detect_stacks(d)
            self.assertEqual(result["known"], [])
            self.assertEqual(result["unsupported"], ["ruby", "rust"])

    def test_empty_dir_returns_empty_lists(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(detect.detect_stacks(d), {"known": [], "unsupported": []})

    def test_missing_dir_returns_empty_lists(self):
        self.assertEqual(detect.detect_stacks("/no/such/dir/xyz"),
                         {"known": [], "unsupported": []})


class TestDetectConsistency(unittest.TestCase):
    def test_marker_values_are_known_stacks(self):
        for key in detect.MARKERS.values():
            self.assertIn(key, stacks.KNOWN)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_detect -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'agentsec.detect'`）

- [ ] **Step 3: 最小実装**

`generator/agentsec/detect.py` を新規作成:

```python
"""対象ディレクトリのマーカーファイルからビルド/言語スタックを検出する純ロジック。

ファイルシステム読み取りのみを行い、対話 I/O は持たない（generate.py 側に置く）。

スタックを増やすときの編集箇所:
  1. agentsec/stacks.py の STACKS（allow/ask コマンド。これが正典）
  2. このファイルの MARKERS（マーカー → スタックキー）
  3. （任意）このファイルの BASE_IMAGES（スタックキー → base-image）
MARKERS の値と BASE_IMAGES のキーは stacks.KNOWN の部分集合でなければならない
（tests/test_detect.py の整合テストで強制）。
"""

import os
from pathlib import Path

# マーカー（ファイル名 or "*.ext" グロブ） → 既知スタックキー（stacks.STACKS と一致）
MARKERS = {
    "package.json": "npm",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "pyproject.toml": "pip",
    "requirements.txt": "pip",
    "setup.py": "pip",
    "Pipfile": "pip",
    "go.mod": "go",
    "*.csproj": "dotnet",
}

# 未対応スタックのマーカー → 表示ラベル（警告に使う。生成はしない）
UNSUPPORTED_MARKERS = {
    "Cargo.toml": "rust",
    "Gemfile": "ruby",
    "composer.json": "php",
}

# 走査時に降りない依存/VCS/成果物ディレクトリ（誤検出と無駄走査を防ぐ）
IGNORE_DIRS = {
    ".git", "node_modules", "vendor", ".venv", "venv", "__pycache__",
    "dist", "build", "target", ".gradle", "bin", "obj", ".next", ".tox",
}

MAX_DEPTH = 3


def _file_matches(filenames, marker):
    if marker.startswith("*."):
        suffix = marker[1:]
        return any(name.endswith(suffix) for name in filenames)
    return marker in filenames


def detect_stacks(target_dir, max_depth=MAX_DEPTH):
    """target_dir 配下を max_depth まで再帰走査し検出スタックの union を返す。

    IGNORE_DIRS と隠しディレクトリ（先頭ドット）は降りない。
    返り値: {"known": [...], "unsupported": [...]}（ともにソート済み・重複なし）。
    ディレクトリが無い場合は空リストを返す。
    """
    root = Path(target_dir)
    if not root.is_dir():
        return {"known": [], "unsupported": []}
    known, unsupported = set(), set()
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth >= max_depth:
            dirnames[:] = []  # これ以上深くは降りない
        else:
            dirnames[:] = [d for d in dirnames
                           if d not in IGNORE_DIRS and not d.startswith(".")]
        for marker, key in MARKERS.items():
            if _file_matches(filenames, marker):
                known.add(key)
        for marker, label in UNSUPPORTED_MARKERS.items():
            if marker in filenames:
                unsupported.add(label)
    return {"known": sorted(known), "unsupported": sorted(unsupported)}
```

- [ ] **Step 4: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_detect -v`
Expected: PASS（11 tests）

- [ ] **Step 5: コミット**

```bash
cd generator && git add agentsec/detect.py tests/test_detect.py
git commit -m "feat: detect stacks from project marker files"
```

---

### Task 2: detect.py — 単一スタックからの base-image 推定（改善12）

**Files:**
- Modify: `generator/agentsec/detect.py`
- Test: `generator/tests/test_detect.py`

**Interfaces:**
- Consumes: なし（同ファイル内に追記）。
- Produces:
  - `detect.DEFAULT_BASE_IMAGE: str` — `"node:20-bookworm-slim"`（generate.py の従来既定と一致）。
  - `detect.BASE_IMAGES: dict[str, str]` — 既知スタックキー → base-image。
  - `detect.base_image_for(stack_keys) -> str | None` — 既知スタックが**ちょうど1つ**のときその image を返す。0個・複数・未知混在は `None`。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_detect.py` の末尾（`if __name__` の前）に追記:

```python
class TestBaseImageInference(unittest.TestCase):
    def test_single_known_stack_infers_image(self):
        self.assertEqual(detect.base_image_for(["pip"]), "python:3.12-slim-bookworm")
        self.assertEqual(detect.base_image_for(["npm"]), "node:20-bookworm-slim")

    def test_multiple_stacks_returns_none(self):
        self.assertIsNone(detect.base_image_for(["npm", "pip"]))

    def test_empty_returns_none(self):
        self.assertIsNone(detect.base_image_for([]))

    def test_unknown_stack_returns_none(self):
        self.assertIsNone(detect.base_image_for(["rust"]))

    def test_default_base_image_matches_cli_default(self):
        self.assertEqual(detect.DEFAULT_BASE_IMAGE, "node:20-bookworm-slim")

    def test_base_image_keys_are_known_stacks(self):
        for key in detect.BASE_IMAGES:
            self.assertIn(key, stacks.KNOWN)
```

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_detect -v`
Expected: FAIL（`AttributeError: module 'agentsec.detect' has no attribute 'base_image_for'`）

- [ ] **Step 3: 最小実装**

`generator/agentsec/detect.py` の `UNSUPPORTED_MARKERS` 定義の直後に追記:

```python
DEFAULT_BASE_IMAGE = "node:20-bookworm-slim"

# 既知スタックキー → 推奨 base-image（単一スタック検出時のみ使う）
BASE_IMAGES = {
    "npm": "node:20-bookworm-slim",
    "pip": "python:3.12-slim-bookworm",
    "go": "golang:1.22-bookworm",
    "maven": "eclipse-temurin:21-jdk",
    "gradle": "eclipse-temurin:21-jdk",
    "dotnet": "mcr.microsoft.com/dotnet/sdk:8.0",
}


def base_image_for(stack_keys):
    """既知スタックがちょうど1つのときその base-image を返す。それ以外は None。"""
    if len(stack_keys) != 1:
        return None
    return BASE_IMAGES.get(stack_keys[0])
```

- [ ] **Step 4: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_detect -v`
Expected: PASS（17 tests）

- [ ] **Step 5: コミット**

```bash
cd generator && git add agentsec/detect.py tests/test_detect.py
git commit -m "feat: infer base image from a single detected stack"
```

---

### Task 3: profile.py — 任意キー base_image の検証と往復保存

**Files:**
- Modify: `generator/agentsec/profile.py:13` 付近（`_OPTIONAL_BOOL_KEYS` の周辺）
- Test: `generator/tests/test_profile.py`

**Interfaces:**
- Consumes: なし。
- Produces: `profile.validate` が `base_image`（存在するなら `str`）を受理する。`save`/`load` で往復する（`build_record` は既存どおり `profile` 全体を記録するので追加変更不要）。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_profile.py` の `TestProfile` クラス内に追記:

```python
    def test_validate_accepts_optional_base_image(self):
        p = self._valid()
        p["base_image"] = "python:3.12-slim-bookworm"
        profile.validate(p)  # raises nothing

    def test_validate_rejects_non_string_base_image(self):
        p = self._valid()
        p["base_image"] = 123
        with self.assertRaises(ValueError):
            profile.validate(p)

    def test_base_image_roundtrips(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "p.json")
            p = self._valid()
            p["base_image"] = "golang:1.22-bookworm"
            profile.save(path, p)
            self.assertEqual(profile.load(path)["base_image"], "golang:1.22-bookworm")
```

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_profile -v`
Expected: FAIL（`test_validate_rejects_non_string_base_image` が AssertionError: ValueError not raised）

- [ ] **Step 3: 最小実装**

`generator/agentsec/profile.py` の `_OPTIONAL_BOOL_KEYS` 定義の直後に追記:

```python
_OPTIONAL_STR_KEYS = ("base_image",)
```

`validate` 関数末尾の `_OPTIONAL_BOOL_KEYS` ループの直後に追記:

```python
    for key in _OPTIONAL_STR_KEYS:
        if key in profile and not isinstance(profile[key], str):
            raise ValueError(f"{key} must be a str when present")
```

- [ ] **Step 4: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_profile -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
cd generator && git add agentsec/profile.py tests/test_profile.py
git commit -m "feat: accept optional base_image in profile schema"
```

---

### Task 4: generate.py — 検出ベースの対話スタック解決

**Files:**
- Modify: `generator/generate.py`（`collect_interactive` のスタック分岐、`--target-dir` 追加、import）
- Test: `generator/tests/test_generate.py`

**Interfaces:**
- Consumes: `detect.detect_stacks(target_dir) -> {"known","unsupported"}`（Task 1）、`stacks.unknown_keys`、`questions.QUESTIONS`。
- Produces:
  - `generate.resolve_stacks_interactive(target_dir, input_fn, print_fn) -> list[str]` — 検出→提示→確認→手動フォールバック/グリーンフィールド選択を行い、最終的なスタックキー列を返す。
  - `collect_interactive(input_fn=input, print_fn=print, target_dir=".")` — スタック分岐を `resolve_stacks_interactive` 経由にする。シグネチャは既存の位置引数 `(input_fn, print_fn)` を壊さないため `target_dir` を**末尾**に追加する。
  - `main` に `--target-dir`（default `"."`）を追加し、`collect_interactive(target_dir=args.target_dir)` を呼ぶ。

検出・確認・手動フォールバックの分岐仕様（`resolve_stacks_interactive`）:
1. `result = detect.detect_stacks(target_dir)`。
2. `result["unsupported"]` があれば警告を1行表示（生成後に手動追加する旨）。
3. `result["known"]` があれば「検出したスタック: …」を表示し、`confirm("これらを使いますか", default=True)` 相当を問う（空 Enter=はい）。はいなら検出結果を返す。いいえなら手動入力へ。
4. 検出ゼロ、または上記で「いいえ」の場合は手動入力：既存の `stacks` 質問（`questions.QUESTIONS` の `key=="stacks"`）を `ask_question` で問い、`stacks.unknown_keys` で未知が残る間は再質問する（既存ロジックを踏襲。空 Enter でスキップ可＝グリーンフィールド）。検出ゼロ時は手動入力前に「検出なし。予定スタックを選択（未定なら空 Enter）」を表示する。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_generate.py` の冒頭 import に `tempfile`/`Path` は既にある。`from agentsec import detect` を import 群に追加し、新しいテストクラスを追記:

```python
class TestResolveStacksInteractive(unittest.TestCase):
    def test_detected_stacks_confirmed_with_empty_enter(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "package.json").write_text("", encoding="utf-8")
            out, pr = sink()
            # 確認に空 Enter（=はい）
            chosen = generate.resolve_stacks_interactive(d, scripted([""]), pr)
            self.assertEqual(chosen, ["npm"])
            self.assertTrue(any("npm" in line for line in out))

    def test_detected_rejected_then_manual_entry(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "package.json").write_text("", encoding="utf-8")
            out, pr = sink()
            # 確認に n（いいえ）→ 手動で go を入力
            chosen = generate.resolve_stacks_interactive(d, scripted(["n", "go"]), pr)
            self.assertEqual(chosen, ["go"])

    def test_unsupported_warns_and_falls_to_manual(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "Cargo.toml").write_text("", encoding="utf-8")
            out, pr = sink()
            # 検出ゼロ（未対応のみ）→ 手動入力（空 Enter でスキップ）
            chosen = generate.resolve_stacks_interactive(d, scripted([""]), pr)
            self.assertEqual(chosen, [])
            self.assertTrue(any("rust" in line for line in out))

    def test_greenfield_zero_detection_manual_with_reask(self):
        with tempfile.TemporaryDirectory() as d:
            out, pr = sink()
            # 検出なし → 未知 rust で再質問 → npm
            chosen = generate.resolve_stacks_interactive(d, scripted(["npm,rust", "npm"]), pr)
            self.assertEqual(chosen, ["npm"])
```

`TestCollectInteractive.test_unknown_stack_warns_and_reasks` は cwd 依存を避けるため `target_dir` を明示する空ディレクトリへ変更する。既存テストを次に置き換える:

```python
class TestCollectInteractive(unittest.TestCase):
    def test_unknown_stack_warns_and_reasks(self):
        with tempfile.TemporaryDirectory() as d:
            # 製品2, level, plan, stacks(不正→正), domains, extra, container, 4 redline
            inputs = ["y", "y", "L2", "team",
                      "npm,rust", "npm",          # stacks: 未知 rust → 再入力
                      "github.com", "",
                      "y", "n", "n", "n", "n"]
            out, pr = sink()
            profile = generate.collect_interactive(scripted(inputs), pr, target_dir=d)
            self.assertEqual(profile["stacks"], ["npm"])
            self.assertTrue(any("rust" in line for line in out))
            self.assertEqual(profile["level"], "L2")
            self.assertEqual(profile["products"], ["claude", "codex"])
```

注: この変更後 `collect_interactive` は base-image 解決（Task 5）を**まだ含まない**ため、上記 `inputs` は base-image 入力を含まない。Task 5 で base-image 解決を足す際にこの inputs を更新する（Task 5 のテスト手順に明記）。

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_generate -v`
Expected: FAIL（`AttributeError: module 'generate' has no attribute 'resolve_stacks_interactive'` ほか）

- [ ] **Step 3: 最小実装**

`generator/generate.py` の import を変更（`detect` を追加）:

```python
from agentsec import (rules, redlines, orchestrate, questions, summary, stacks,
                      detect, profile as profile_mod)
```

`ask_question` の直後に `resolve_stacks_interactive` を追加:

```python
def _stacks_question():
    return next(q for q in questions.QUESTIONS if q["key"] == "stacks")


def _manual_stacks(input_fn, print_fn):
    q = _stacks_question()
    while True:
        chosen = ask_question(q, input_fn, print_fn)
        unknown = stacks.unknown_keys(chosen)
        if not unknown:
            return chosen
        print_fn(f"  未対応のスタックです: {', '.join(unknown)}。"
                 f"対応: {', '.join(sorted(stacks.KNOWN))}。"
                 f"未対応分は空にして生成後に手動追加してください。")


def resolve_stacks_interactive(target_dir, input_fn=input, print_fn=print):
    result = detect.detect_stacks(target_dir)
    if result["unsupported"]:
        print_fn(f"  未対応スタックを検出: {', '.join(result['unsupported'])}。"
                 f"これらは生成後に手動で追加してください。")
    if result["known"]:
        print_fn(f"  検出したスタック: {', '.join(result['known'])}")
        if confirm("これらを使いますか", input_fn, default=True):
            return result["known"]
    else:
        print_fn("  スタックを検出できませんでした。予定スタックを選択してください"
                 "（未定なら空 Enter でスキップ）。")
    return _manual_stacks(input_fn, print_fn)
```

`collect_interactive` のシグネチャと stacks 分岐を変更:

```python
def collect_interactive(input_fn=input, print_fn=print, target_dir="."):
    a = {}
    for q in questions.QUESTIONS:
        if q["key"] == "stacks":
            a["stacks"] = resolve_stacks_interactive(target_dir, input_fn, print_fn)
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
```

注: `confirm` は `resolve_stacks_interactive` より上（ファイル内）で定義されている必要がある。現状 `confirm` は `collect_interactive` の後にあるため、`confirm` 定義を `ask_question` の直後（`resolve_stacks_interactive` の前）へ移動する。移動のみで本体は変更しない:

```python
def confirm(prompt, input_fn=input, default=True):
    suffix = " [Y/n]: " if default else " [y/N]: "
    raw = input_fn(prompt + suffix).strip().lower()
    if raw == "":
        return default
    return raw == "y"
```

`main` の argparse に `--target-dir` を追加し、`collect_interactive` 呼び出しを変更:

```python
    parser.add_argument("--target-dir", default=".")
```

```python
        profile = collect_interactive(target_dir=args.target_dir)
```

- [ ] **Step 4: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_generate -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
cd generator && git add generate.py tests/test_generate.py
git commit -m "feat: resolve stacks via detection in interactive mode"
```

---

### Task 5: generate.py — base-image の解決と profile 保存

**Files:**
- Modify: `generator/generate.py`（`collect_interactive` に base-image 解決を追加、`--base-image` default を `None` に、`main` の base-image 優先順位）
- Test: `generator/tests/test_generate.py`

**Interfaces:**
- Consumes: `detect.base_image_for(stack_keys)`、`detect.DEFAULT_BASE_IMAGE`（Task 2）、`confirm`（Task 4 で前方移動済み）。
- Produces:
  - `collect_interactive(..., target_dir=".", base_image_override=None)` — 質問ループ後に base-image を解決し `profile["base_image"]` に格納する。
  - base-image 優先順位（対話）: `base_image_override`（明示）> 単一スタック推定を確認採用 > `detect.DEFAULT_BASE_IMAGE`。`use_container` が False のときは推定の問い合わせをせず override か DEFAULT を入れる。
  - `main`: `--base-image` の default を `None` にする。`--profile` 経路の base-image 優先順位: `args.base_image`（明示）> `profile.get("base_image")` > `detect.DEFAULT_BASE_IMAGE`。解決値を `orchestrate.generate(profile, ..., base_image)` に渡す。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_generate.py` に追記:

```python
class TestBaseImageResolution(unittest.TestCase):
    def test_single_stack_inferred_image_confirmed(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "go.mod").write_text("", encoding="utf-8")
            out, pr = sink()
            # 製品2, level, plan, [stacks: 検出 go を確認=空Enter],
            # domains, extra, container=y, 4 redline, base-image 確認=空Enter
            inputs = ["y", "y", "L2", "team",
                      "",                         # 検出 go を採用
                      "github.com", "",
                      "y", "n", "n", "n", "n",
                      ""]                          # 推定 base-image を採用
            profile = generate.collect_interactive(scripted(inputs), pr, target_dir=d)
            self.assertEqual(profile["stacks"], ["go"])
            self.assertEqual(profile["base_image"], "golang:1.22-bookworm")

    def test_no_container_uses_default_without_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "go.mod").write_text("", encoding="utf-8")
            out, pr = sink()
            # container=n のときは base-image を問わない（余分な入力なし）
            inputs = ["y", "y", "L2", "team",
                      "",                         # 検出 go を採用
                      "github.com", "",
                      "n", "n", "n", "n", "n"]    # container=n + 4 redline
            profile = generate.collect_interactive(scripted(inputs), pr, target_dir=d)
            self.assertEqual(profile["base_image"], detect.DEFAULT_BASE_IMAGE)

    def test_profile_base_image_used_on_regen(self):
        with tempfile.TemporaryDirectory() as d:
            src = {"products": ["claude"], "level": "L2", "plan": "personal",
                   "stacks": ["go"], "allowed_domains": ["github.com"],
                   "extra_deny_paths": [], "use_container": True,
                   "base_image": "golang:1.22-bookworm"}
            (Path(d) / "in.json").write_text(json.dumps(src), encoding="utf-8")
            rc = generate.main(["--profile", str(Path(d) / "in.json"),
                                "--output", str(Path(d) / "out")])
            self.assertEqual(rc, 0)
            dockerfile = (Path(d) / "out" / "Dockerfile").read_text(encoding="utf-8")
            self.assertIn("golang:1.22-bookworm", dockerfile)
```

`TestCollectInteractive.test_unknown_stack_warns_and_reasks` の `inputs` 末尾に base-image 確認の空 Enter を1つ追加する（container=y のため推定問い合わせが入るが、複数スタックでない単一 npm のため推定が走る）。次に置き換える:

```python
            inputs = ["y", "y", "L2", "team",
                      "npm,rust", "npm",          # stacks: 未知 rust → 再入力
                      "github.com", "",
                      "y", "n", "n", "n", "n",
                      ""]                          # 推定 base-image を採用
```

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_generate -v`
Expected: FAIL（`KeyError: 'base_image'` ほか）

- [ ] **Step 3: 最小実装**

`generator/generate.py` の `collect_interactive` シグネチャと末尾の return 直前を変更。シグネチャ:

```python
def collect_interactive(input_fn=input, print_fn=print, target_dir=".",
                        base_image_override=None):
```

質問ループ後（`products` 構築の前後どちらでも可、return の前）に base-image 解決を追加:

```python
    base_image = _resolve_base_image(
        a["stacks"], a["use_container"], base_image_override, input_fn, print_fn)
```

return 辞書に `"base_image": base_image,` を追加する。

`resolve_stacks_interactive` の直後に `_resolve_base_image` を追加:

```python
def _resolve_base_image(stack_keys, use_container, override, input_fn, print_fn):
    if override:
        return override
    if not use_container:
        return detect.DEFAULT_BASE_IMAGE
    inferred = detect.base_image_for(stack_keys)
    if inferred:
        print_fn(f"  推奨ベースイメージ: {inferred}")
        if confirm("これを使いますか", input_fn, default=True):
            return inferred
    return detect.DEFAULT_BASE_IMAGE
```

`main` の argparse を変更（default を None に）:

```python
    parser.add_argument("--base-image", default=None)
```

`main` の対話分岐を変更（`collect_interactive` に override を渡す）:

```python
        profile = collect_interactive(target_dir=args.target_dir,
                                      base_image_override=args.base_image)
```

`main` で `orchestrate.generate` に渡す base-image を解決する。`files = orchestrate.generate(...)` の直前に追加:

```python
    base_image = (args.base_image or profile.get("base_image")
                  or detect.DEFAULT_BASE_IMAGE)
```

`orchestrate.generate` 呼び出しの `args.base_image` を `base_image` に変更:

```python
    files = orchestrate.generate(profile, args.output, devs, base_image)
```

- [ ] **Step 4: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_generate -v`
Expected: PASS

- [ ] **Step 5: 全テスト確認**

Run: `cd generator && python3 -m unittest discover -s tests`
Expected: OK（全テスト通過）

- [ ] **Step 6: コミット**

```bash
cd generator && git add generate.py tests/test_generate.py
git commit -m "feat: resolve and persist base image from detected stack"
```

---

### Task 6: 配置スコープの明確化 — README に配置/優先順位/R6 ガイド

**Files:**
- Modify: `generator/agentsec/readme.py`（`placement_guide` 追加）
- Modify: `generator/agentsec/orchestrate.py`（`text_map` に `placement_guide` を追加）
- Modify: `generator/templates/policy/README.md.tmpl`（`$placement_guide` 節を追加）
- Test: `generator/tests/test_readme.py`、`generator/tests/test_orchestrate.py`

**背景:** 設定の区別軸は「コンテナ全体 vs プロジェクト単位」という場所ではなく**強制力（解除可否）と信頼**。守らせたい統制は最上位（管理層）へリポジトリ外から配置すべきで、プロジェクト層の `.claude/`・`.codex/` はエージェント自身が書き換え可能なため強制ポリシーとみなせない（`docs/00-red-lines.md` R6、`docs/11-claude-code.md:71`、`docs/10-codex.md:219`）。優先順位は管理 > プロジェクト > ユーザー。現状の `artifact_guide` はファイル個別の配置に触れるが、層・優先順位・R6 注記をまとめた節が無いので追加する。

**Interfaces:**
- Consumes: なし。
- Produces: `readme.placement_guide(file_keys) -> str` — 生成された成果物の集合に応じて配置3層の表と優先順位・R6 注記を返す純関数。`orchestrate` が `text_map["placement_guide"]` として渡し、README テンプレの `$placement_guide` に展開する。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_readme.py` に追記:

```python
class TestPlacementGuide(unittest.TestCase):
    def test_managed_row_and_precedence_when_managed_present(self):
        out = readme.placement_guide({"claude-code/managed-settings.json"})
        self.assertIn("リポジトリ外", out)
        self.assertIn("管理 > プロジェクト > ユーザー", out)

    def test_r6_caveat_always_present(self):
        out = readme.placement_guide({"codex/.codex/config.toml"})
        self.assertIn("R6", out)
        self.assertIn("強制ポリシーとみなさない", out)

    def test_managed_row_absent_without_managed_files(self):
        out = readme.placement_guide({"claude-code/.claude/settings.json"})
        self.assertNotIn("OS 管理パス", out)
```

`generator/tests/test_orchestrate.py` に、README へ配置ガイドが入ることを確認するテストを追記（既存の生成テストの近くに置く。`profile`/`generate` 呼び出しの形は既存テストに合わせる）:

```python
    def test_readme_includes_placement_guide(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            profile = {"products": ["claude"], "level": "L3", "plan": "team",
                       "stacks": ["npm"], "allowed_domains": ["github.com"],
                       "extra_deny_paths": [], "use_container": False}
            orchestrate.generate(profile, d, [], "node:20-bookworm-slim")
            readme_text = (Path(d) / "README.md").read_text(encoding="utf-8")
            self.assertIn("配置と優先順位", readme_text)
            self.assertIn("R6", readme_text)
```

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_readme tests.test_orchestrate -v`
Expected: FAIL（`AttributeError: module 'agentsec.readme' has no attribute 'placement_guide'`、README に「配置と優先順位」が無い）

- [ ] **Step 3: 最小実装**

`generator/agentsec/readme.py` の末尾に追記:

```python
def placement_guide(file_keys):
    """生成成果物に応じて配置3層・優先順位・R6 注記を返す（純関数）。"""
    has_managed = ("claude-code/managed-settings.json" in file_keys
                   or "codex/requirements.toml" in file_keys)
    has_local = ("claude-code/.claude/settings.json" in file_keys
                 or "codex/.codex/config.toml" in file_keys)
    lines = ["設定は強制力で層が分かれます。**守らせたい統制は最上位（管理層）へ"
             "リポジトリ外から配置**してください（docs/00 R6）。", "",
             "| 層 | 強制力 | 配置先 |", "|---|---|---|"]
    if has_managed:
        lines.append("| 管理 | 利用者/エージェントが解除不能 | "
                     "**リポジトリ外**（OS 管理パス・MDM・コンテナイメージ） |")
    if has_local:
        lines.append("| プロジェクト/ユーザー | 書き換え可能＝強制ではない | "
                     "リポジトリ内 `.claude/` ／ コンテナ home `~/.codex/` |")
    lines += ["",
              "- 優先順位: **管理 > プロジェクト > ユーザー**。ガードレールは管理層に置き、"
              "`*ManagedOnly` 系で下位層からの再許可を抑止する。",
              "- **R6**: `.claude/`・`.codex/`・`CLAUDE.md`・`AGENTS.md` 等はリポジトリを"
              "書ける主体（エージェント自身を含む）が変更できるため、**強制ポリシーとみなさない**。",
              "- スタック別 allow/ask（`npm test` 等）はプロジェクト層の補助。"
              "レッドライン・egress 許可・資格情報 denyRead は管理層で固定する。"]
    return "\n".join(lines)
```

`generator/agentsec/orchestrate.py` の `text_map` に1行追加（`"apply_steps": readme.apply_steps(artifact_keys),` の直後）:

```python
        "placement_guide": readme.placement_guide(artifact_keys),
```

`generator/templates/policy/README.md.tmpl` の「## 適用」節の直前に追加:

```markdown
## 配置と優先順位（重要）

$placement_guide

```

- [ ] **Step 4: 通過を確認**

Run: `cd generator && python3 -m unittest tests.test_readme tests.test_orchestrate -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
cd generator && git add agentsec/readme.py agentsec/orchestrate.py templates/policy/README.md.tmpl tests/test_readme.py tests/test_orchestrate.py
git commit -m "feat: document config placement scopes and precedence in readme"
```

---

### Task 7: 統合スモーク & ドキュメント追記

**Files:**
- Modify: `CLAUDE.md`（変更後の検証スニペットに `--target-dir` 例を追記）
- Test: `generator/tests/test_generate.py`（`--target-dir` end-to-end スモーク1本）

**Interfaces:**
- Consumes: `main(argv)`（Task 4/5）、`detect`、`orchestrate`。
- Produces: なし（検証とドキュメントのみ）。

- [ ] **Step 1: 失敗するテストを書く**

`generator/tests/test_generate.py` に追記。`--target-dir` を渡した対話生成が検出スタックを反映して生成まで完走することを確認する:

```python
class TestTargetDirEndToEnd(unittest.TestCase):
    def test_target_dir_detection_drives_generation(self):
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "proj"
            proj.mkdir()
            (proj / "go.mod").write_text("", encoding="utf-8")
            out = Path(d) / "out"
            # main は対話時 input() を直接使い注入できないため、検出→collect→
            # orchestrate を直接呼んで end-to-end を検証する（--profile 経路の
            # base-image 再現は Task 5 の test_profile_base_image_used_on_regen が担保）。
            # claude のみ, L2, personal, [検出 go 採用=空Enter],
            # domains, extra, container=y, 4 redline, base-image 採用=空Enter
            inputs = ["y", "n", "L2", "personal",
                      "",
                      "github.com", "",
                      "y", "n", "n", "n", "n",
                      ""]
            _, pr = sink()
            profile = generate.collect_interactive(scripted(inputs), pr,
                                                   target_dir=str(proj))
            self.assertEqual(profile["stacks"], ["go"])
            self.assertEqual(profile["base_image"], "golang:1.22-bookworm")
            generate.orchestrate.generate(profile, str(out), [], profile["base_image"])
            dockerfile = (out / "Dockerfile").read_text(encoding="utf-8")
            self.assertIn("golang:1.22-bookworm", dockerfile)
            self.assertIn("Bash(go test *)",
                          (out / "claude-code/.claude/settings.json").read_text(encoding="utf-8"))
```

注: `main` は対話時 `input()` を直接使い注入できないため、このスモークは `collect_interactive` + `orchestrate.generate` を直接呼んで end-to-end を検証する（`main` の `--profile` 経路は Task 5 の `test_profile_base_image_used_on_regen` が担保済み）。`inputs` の生成確認用末尾要素は使わないので除去する形に整理してよい。

- [ ] **Step 2: 失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_generate -v`
Expected: 既存実装で stacks/base_image は通るはずだが、テスト未追加状態からの追加なので追加後に PASS することを確認（FAIL する場合は実装側ではなくテスト記述の不整合を修正）。

- [ ] **Step 3: ドキュメント追記**

`CLAUDE.md` の「変更後の検証」節のスモーク例の下に `--target-dir` の使い方を1行追記:

```bash
# 対話生成で対象プロジェクトを自動検出（カレント以外を見る場合）
python3 generate.py --target-dir /path/to/project --output /tmp/gen-detect
```

- [ ] **Step 4: 全テスト & スモーク確認**

Run:
```bash
cd generator && python3 -m unittest discover -s tests
python3 generate.py --profile profiles/examples/L2-team-both.json --output /tmp/gen-smoke
python3 /tmp/gen-smoke/acceptance/selfcheck.py /tmp/gen-smoke
```
Expected: テスト OK、生成成功、selfcheck exit 0。

- [ ] **Step 5: コミット**

```bash
cd /Users/a160341/Documents/_work/coding-agent-security-work
git add generator/tests/test_generate.py CLAUDE.md
git commit -m "test: cover target-dir detection end to end and document flag"
```

---

## Self-Review

**1. Spec coverage:**
- 課題3（スタック手動列挙の負担）→ Task 1（検出）+ Task 4（対話提示/確認/フォールバック）。✅
- 検出マーカー対応表 → Task 1 `MARKERS`/`UNSUPPORTED_MARKERS`。✅
- モノレポ/複数プロジェクトのマウント → Task 1 で `max_depth` まで再帰し `IGNORE_DIRS`・隠しディレクトリを枝刈りした上で検出スタックの **union** を返す（`test_unions_across_subprojects`/`test_monorepo_nested_packages`/`test_ignores_dependency_dirs`/`test_respects_max_depth`）。生成設定はコンテナ単位で1つなので union が正しい意味論。✅
- スタック追加のしやすさ → 追加はデータ（`STACKS`/`MARKERS`/`BASE_IMAGES`）への追記のみ。ドリフトは整合テスト `test_marker_values_are_known_stacks`/`test_base_image_keys_are_known_stacks` が FAIL で検出。✅
- 未対応スタックは警告して続行 → Task 1（reported）+ Task 4（警告表示）。✅
- 検出ゼロ/グリーンフィールドは予定スタック選択＋スキップ → Task 4 Step 3 分岐4。✅
- `--target-dir`（既定=カレント）→ Task 4。✅
- `--profile` 再生は profile 優先・検出は対話のみ → Task 5（main の `--profile` 経路は検出を呼ばない）+ Global Constraints。✅
- 改善12（単一スタック時のみ base-image 推定、複数/未検出は既定、`--base-image` 最優先）→ Task 2 + Task 5。✅
- base_image を profile に保存・再生で再現 → Task 3 + Task 5 `test_profile_base_image_used_on_regen`。✅
- 配置スコープ明確化（強制力3層・優先順位・R6＝プロジェクト設定は強制でない）→ Task 6 `readme.placement_guide` + README テンプレ `$placement_guide`（`test_readme_includes_placement_guide`）。✅

**2. Placeholder scan:** プレースホルダなし。全ステップに具体コード/コマンド/期待出力あり。Task 6 Step 1 のテストは `main` が input を注入できない制約を明示し、回避方法（collect+orchestrate 直呼び）を具体コードで提示済み。

**3. Type consistency:**
- `detect.detect_stacks(target_dir, max_depth=MAX_DEPTH)` 返り値 `{"known","unsupported"}` は Task 1/4 で一致（Task 4 は既定 `max_depth` で呼ぶ）。
- `detect.base_image_for(stack_keys) -> str|None` は Task 2/5 で一致。
- `detect.DEFAULT_BASE_IMAGE` は Task 2 定義、Task 5/6 で参照、値 `"node:20-bookworm-slim"` は generate.py 既存既定と一致。
- `resolve_stacks_interactive(target_dir, input_fn, print_fn)` は Task 4 定義・テストで一致。
- `collect_interactive(input_fn, print_fn, target_dir, base_image_override)` の引数順は既存位置引数 `(input_fn, print_fn)` を保持しつつ末尾追加で後方互換。✅
- `confirm` を前方移動する依存（Task 4）を明記済み。
