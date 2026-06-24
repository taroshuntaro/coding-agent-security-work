# 2026-06 製品アップデート反映 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 2026-06-20 以降の Claude Code / Codex 更新を本ガイドの正典値と generator に反映する。

**Architecture:** docs の値更新を主体に、generator は `requiredMinimumVersion`（profile 指定時のみ生成）の1点だけ変更する。資格情報ガードの新手段・新管理キーは docs 記載に留める（YAGNI／非専門ユーザー向け最小助言設定の維持）。各値は実装時に公式一次資料で再確認し、付録C の確認日を更新する。

**Tech Stack:** Markdown（docs）、Python 3.11 標準ライブラリのみ（generator）、`unittest`。

## Global Constraints

- Python 3.11 以上、標準ライブラリのみ。サードパーティ依存を追加しない。
- TOML 書き込みは `agentsec/render_toml.py`。`tomllib` は読み取り専用。
- `agentsec/selfcheck.py` は standalone を保つ（`from agentsec import ...` を入れない）。
- テストは標準 `unittest`。実行: `cd generator && python3 -m unittest discover -s tests`。
- 改行は LF、パス操作は `pathlib`、ファイル I/O は `encoding="utf-8"`。
- docs の値 ＝ generator 生成設定を一致させる。レッドライン生成拒否ロジックは変更しない。
- **二次資料のみの項目（R1）は、一次資料で closed を確認できない限りセキュリティ警告のトーンを弱めない。**
- 付録C の基準確認日を **2026-06-24** に更新。一次資料で確認できない値は ⚠️ 据え置き。
- 作業ブランチ: `docs/product-updates-2026h1`（作成済み）。
- コミットメッセージは英語・Conventional Commits。共著表記は `Co-authored-by: Claude <noreply@anthropic.com>`。

---

## フェーズ1: 高影響（docs 値の更新）

### Task 1: フェーズ1値の一次資料再確認

**Files:**
- 参照のみ（編集なし）。確認結果は Task 2/3 で使用。

- [ ] **Step 1: 公式 sandboxing / env-vars docs を取得して以下を確認**

確認項目（URL）:
- `https://code.claude.com/docs/en/sandboxing` — `sandbox.filesystem.allowRead` の存在と、`denyRead:["~/"]＋allowRead:["."]` が**プロジェクト設定でのみ** `"."` がプロジェクトルートに解決される旨。
- `https://code.claude.com/docs/en/env-vars` — `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` の存在と役割（サブプロセス環境変数から Anthropic・クラウド資格情報を除去）。
- `https://code.claude.com/docs/en/settings` — `sandbox.credentials` が settings リファレンスに掲載されているか（掲載が無ければ ⚠️ 据え置き）。

- [ ] **Step 2: 二次資料項目（R1）の一次確認**

- `https://github.com/anthropics/claude-code/issues/29016` と `/43713` の state（open/closed）と、closed なら修正バージョン。
- 公式 CHANGELOG（`https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`）で「複合 Bash／env-var プレフィックス／`/dev/tcp`／パイプ `cd`」のバイパス修正、および「PreToolUse hook の `allow` が deny を上書きするバグ修正」の記載とバージョンを確認。

- [ ] **Step 3: 確認結果を作業メモに記録**

各項目を `確認済み（✅, 出典URL, バージョン）` / `未確認（⚠️ 据え置き）` に仕分けてメモする（コミット不要、Task 2/3 の分岐に使う）。

---

### Task 2: 資格情報ガードの新手段を docs に反映

**Files:**
- Modify: `docs/11-claude-code.md`（11.4 の `settings.json` 例の後、11.4 の箇条書き、11.5 注意）
- Modify: `docs/08-secrets.md`（8.1 付近に env scrub 観点を追記）
- Modify: `docs/appendix-c-volatile-values.md`（C.2 に行追加）

**Interfaces:**
- Consumes: Task 1 Step 1 の確認結果。
- Produces: docs 側の新キー記載。generator は変更しない（後述の理由を 11.4 に明記）。

- [ ] **Step 1: 11.4 に堅牢な denyRead パターンを追記**

`docs/11-claude-code.md` の 11.4 末尾の箇条書き（`autoAllowBashIfSandboxed` の項の前後）に次を追加する:

```markdown
- より強くホーム配下全体の読み取りを遮断したい場合、**プロジェクト `settings.json` に限り** `sandbox.filesystem.denyRead` に `~/`、`sandbox.filesystem.allowRead` に `.` を指定し、ホーム全体を遮断してプロジェクトのみ再許可できる。`allowRead` の `.` は**プロジェクト設定でのみ**プロジェクトルートに解決される。`~/.claude/settings.json` や `managed-settings.json` に同じ指定を置くと `.` は `~/.claude` に解決され意図がずれるため、グローバル・管理設定では従来どおり `~/.ssh`・`~/.aws`・`~/.kube` を明示列挙する。ホーム配下のツールチェインやキャッシュ読み取りを必要とするビルドでは `~/` 全遮断が失敗の原因になり得るため、案件のビルド要件を確認してから採用する。
```

- [ ] **Step 2: 08-secrets.md に env scrub 観点を追記**

`docs/08-secrets.md` の 8.1 の箇条書き「環境変数も、`env`、`printenv`、子プロセス、デバッグログから読める。」の直後に追加する:

```markdown
- ファイルの read deny だけでは環境変数経由の資格情報は残る。Claude Codeでは `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` でサンドボックス内サブプロセスの環境変数からAnthropic・クラウド資格情報を除去できる（[付録C](appendix-c-volatile-values.md)、適用前に対象バージョンで確認）。
```

- [ ] **Step 3: appendix-c C.2 に行追加**

`docs/appendix-c-volatile-values.md` の C.2 表に次の行を追加する（`sandbox.credentials` は Task 1 で settings リファレンス未掲載なら ⚠️、掲載確認できたら ✅・確認日 2026-06-24）:

```markdown
| `sandbox.filesystem.allowRead` | `denyRead` 領域内の再許可。`.` はプロジェクト設定でのみプロジェクトルートに解決 | ✅ | 2026-06-24 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | サブプロセス環境変数からAnthropic・クラウド資格情報を除去 | ✅ | 2026-06-24 | [env-vars](https://code.claude.com/docs/en/env-vars) |
| `sandbox.credentials` | 資格情報ファイル＋シークレット環境変数の読取を一括ブロック（CHANGELOG報告。要正式確認） | ⚠️ | — | 導入時に[settings](https://code.claude.com/docs/en/settings)で確認 |
```

- [ ] **Step 4: generator を変更しない理由を 11.4 に1文明記**

11.4 の `settings.json` 例の直後の説明文に、generator が明示列挙を既定とする理由を残す（docs↔generator 整合の説明）:

```markdown
- 生成ツール（`generator/`）の `settings.json` は摩擦の小さい明示列挙（`~/.ssh`・`~/.aws`・`~/.kube`）を既定とする。上記の `~/` 全遮断はより強い代替であり、案件要件に応じて手動で切り替える。
```

- [ ] **Step 5: 整合スモークとコミット**

```bash
cd generator && python3 -m unittest discover -s tests
python3 generate.py --profile profiles/examples/L2-team-both.json --output /tmp/gen-smoke
python3 /tmp/gen-smoke/acceptance/selfcheck.py /tmp/gen-smoke   # exit 0
```

Expected: テスト全通過・selfcheck exit 0（generator 未変更のため挙動不変）。

```bash
cd /Users/a160341/Documents/_work/coding-agent-security-work
git add docs/11-claude-code.md docs/08-secrets.md docs/appendix-c-volatile-values.md
git commit -m "docs: add credential-read guards (allowRead/env scrub)" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

### Task 3: バイパス記述の更新（R1 ゲート）

**Files:**
- Modify: `docs/11-claude-code.md`（11.4）
- Modify: `docs/13-mcp-plugins-hooks.md`
- Modify: `docs/appendix-c-volatile-values.md`（C.2）

**Interfaces:**
- Consumes: Task 1 Step 2 の確認結果。

- [ ] **Step 1: 確認結果で分岐**

- **closed が一次資料で確認できた場合**: 11.4 / C.2 の該当記述に「v\<確認バージョン\> で対処済み（確認日 2026-06-24、出典）」を**追記**する。既存の「受入テスト必須」警告は残す。13 に PreToolUse hook 修正を確認日付きで記載。
- **確認できない場合**: トーンを変えず、C.2 の検証状態欄に「関連バイパスが対処された模様・要検証（2026-06-24）」を併記するに留める。**11.4 本文の警告トーンは変更しない。**

11.4 の `autoAllowBashIfSandboxed` の項に追記する文（closed 確認時のみ）:

```markdown
  なお、複合コマンド・env-varプレフィックス・`/dev/tcp`リダイレクト・パイプ`cd`による一部バイパスは v<確認バージョン> で対処されたと報告されている（確認日 2026-06-24）。挙動はバージョン依存のため受入テストでの確認は引き続き必須とする。
```

13 に追記する文（closed 確認時のみ、13.2 の後ろ）:

```markdown
> [!NOTE]
> PreToolUse hook が `allow` を返すことで deny 権限ルール（管理設定を含む）を上書きできた不具合は v<確認バージョン> で修正されている（確認日 2026-06-24）。Hook の戻り値で deny を無効化できない前提に依存せず、deny は権限ルール側で担保する。
```

- [ ] **Step 2: コミット**

```bash
git add docs/11-claude-code.md docs/13-mcp-plugins-hooks.md docs/appendix-c-volatile-values.md
git commit -m "docs: record sandbox/hook bypass fixes pending verification" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

## フェーズ2: 中影響（新キー記載 ＋ generator 最小反映）

### Task 4: generator に `requiredMinimumVersion`（profile 指定時のみ生成）

**Files:**
- Modify: `generator/agentsec/profile.py`（`_OPTIONAL_STR_KEYS`）
- Modify: `generator/agentsec/build_claude.py`（`build_managed_settings` 署名と本体）
- Modify: `generator/agentsec/orchestrate.py`（profile から値を渡す）
- Test: `generator/tests/test_build_claude.py`、`generator/tests/test_orchestrate.py`

**Interfaces:**
- Produces: `build_managed_settings(level, stacks_keys, allowed_domains, extra_deny_paths, denied_domains, claude_min_version=None)` — `claude_min_version` が truthy のとき出力 dict に `"requiredMinimumVersion": claude_min_version` を含める。未指定なら含めない。
- Consumes: profile 任意キー `claude_min_version`（str）。

- [ ] **Step 1: profile.py の任意 str キーに追加（失敗テスト）**

`generator/tests/test_profile.py` に追加:

```python
def test_claude_min_version_must_be_str(self):
    p = _valid_profile()
    p["claude_min_version"] = 1
    with self.assertRaises(ValueError):
        profile.validate(p)

def test_claude_min_version_str_ok(self):
    p = _valid_profile()
    p["claude_min_version"] = "2.1.163"
    profile.validate(p)  # raises しなければ OK
```

（`_valid_profile()` が無ければ既存テストの有効プロファイル生成ヘルパに合わせる。）

- [ ] **Step 2: テスト失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_profile -v`
Expected: FAIL（`claude_min_version` が未対応で `test_claude_min_version_must_be_str` が AssertionError）

- [ ] **Step 3: profile.py を変更**

`generator/agentsec/profile.py` の `_OPTIONAL_STR_KEYS` を変更:

```python
_OPTIONAL_STR_KEYS = ("base_image", "claude_min_version")
```

- [ ] **Step 4: テスト通過を確認**

Run: `cd generator && python3 -m unittest tests.test_profile -v`
Expected: PASS

- [ ] **Step 5: build_managed_settings の失敗テスト**

`generator/tests/test_build_claude.py` に追加:

```python
def test_managed_settings_omits_required_version_by_default(self):
    s = build_claude.build_managed_settings("L3", ["node"], ["github.com"], [], [])
    self.assertNotIn("requiredMinimumVersion", s)

def test_managed_settings_includes_required_version_when_given(self):
    s = build_claude.build_managed_settings(
        "L3", ["node"], ["github.com"], [], [], claude_min_version="2.1.163")
    self.assertEqual(s["requiredMinimumVersion"], "2.1.163")
```

- [ ] **Step 6: テスト失敗を確認**

Run: `cd generator && python3 -m unittest tests.test_build_claude -v`
Expected: FAIL（`build_managed_settings` が `claude_min_version` 引数を受け取らず TypeError）

- [ ] **Step 7: build_claude.py を変更**

`generator/agentsec/build_claude.py` の `build_managed_settings` 署名と末尾を変更する。署名に `claude_min_version=None` を追加し、return する dict を組み立て後に条件付きでキーを足す:

```python
def build_managed_settings(level, stacks_keys, allowed_domains, extra_deny_paths,
                           denied_domains, claude_min_version=None):
    prof = rules.level_profile(level)
    cmds = stacks.commands_for(stacks_keys)
    settings = {
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
    if claude_min_version:
        settings["requiredMinimumVersion"] = claude_min_version
    return settings
```

- [ ] **Step 8: テスト通過を確認**

Run: `cd generator && python3 -m unittest tests.test_build_claude -v`
Expected: PASS

- [ ] **Step 9: orchestrate.py で profile から値を渡す**

`generator/agentsec/orchestrate.py` の `build_managed_settings` 呼び出し（現 55 行付近）を変更:

```python
            files["claude-code/managed-settings.json"] = _write(
                output_dir, "claude-code/managed-settings.json",
                _json(build_claude.build_managed_settings(
                    lvl, stacks_keys, domains, extra, [],
                    claude_min_version=profile.get("claude_min_version"))))
```

- [ ] **Step 10: orchestrate のエンドツーエンドテスト**

`generator/tests/test_orchestrate.py` に追加（既存の生成テストの書式に合わせる。team+L3 プロファイルを使い、`claude_min_version` 指定時に managed-settings.json に出ることを確認）:

```python
def test_managed_settings_carries_min_version(self):
    prof = _team_l3_profile()  # 既存ヘルパ or インラインで products=["claude"], level="L3", plan="team"
    prof["claude_min_version"] = "2.1.163"
    with tempfile.TemporaryDirectory() as d:
        orchestrate.generate(prof, d, [], "python:3.12-slim")
        data = json.loads(
            (Path(d) / "claude-code/managed-settings.json").read_text(encoding="utf-8"))
        self.assertEqual(data["requiredMinimumVersion"], "2.1.163")
```

- [ ] **Step 11: 全テスト＋スモーク**

Run:
```bash
cd generator && python3 -m unittest discover -s tests
python3 generate.py --profile profiles/examples/L3-team-both.json --output /tmp/gen-min
python3 /tmp/gen-min/acceptance/selfcheck.py /tmp/gen-min   # exit 0
```
Expected: 全 PASS・selfcheck exit 0（`claude_min_version` 未指定の例なので managed-settings に当該キーは出ない）。

- [ ] **Step 12: docs（11.5 / 17.2 / appendix-c）に記載**

`docs/11-claude-code.md` 11.5 の `managed-settings.json` 例の注意書きに追加:

```markdown
- `requiredMinimumVersion`（必要なら `requiredMaximumVersion`）を設定すると、許可バージョン範囲外のクライアント起動を拒否でき、「管理設定が古いクライアントで無視される」問題（[17.2](17-periodic-review.md)）を製品側で防げる。生成ツールは profile の `claude_min_version` を指定したときのみ出力する（既定値は持たない）。
```

`docs/17-periodic-review.md` 17.2 の「管理設定が古いクライアントで無視されないか」に補足:

```markdown
- 管理設定が古いクライアントで無視されないか（Claude Code は `requiredMinimumVersion` で範囲外起動を拒否できる。Codex は全台の対応バージョンを別途確認）
```

`docs/appendix-c-volatile-values.md` C.2 に行追加:

```markdown
| `requiredMinimumVersion` / `requiredMaximumVersion` | 許可バージョン範囲外のクライアント起動を拒否 | ✅ | 2026-06-24 | [settings](https://code.claude.com/docs/en/settings) |
```

- [ ] **Step 13: コミット**

```bash
cd /Users/a160341/Documents/_work/coding-agent-security-work
git add generator/agentsec/profile.py generator/agentsec/build_claude.py generator/agentsec/orchestrate.py generator/tests/ docs/11-claude-code.md docs/17-periodic-review.md docs/appendix-c-volatile-values.md
git commit -m "feat: emit requiredMinimumVersion when profile pins it" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

### Task 5: `deniedMcpServers` / モデル許可リストを docs に記載（generator 生成なし）

**Files:**
- Modify: `docs/11-claude-code.md`（11.5）
- Modify: `docs/13-mcp-plugins-hooks.md`
- Modify: `docs/appendix-c-volatile-values.md`（C.2）

- [ ] **Step 1: 11.5 注意に追記**

`docs/11-claude-code.md` 11.5 の注意書きに追加:

```markdown
- `allowedMcpServers` の許可リストに加え、`deniedMcpServers` で特定サーバーを明示拒否できる（denylist が優先）。
- `availableModels` と `enforceAvailableModels: true` で、利用可能モデルを許可リストへ固定できる。データ越境・コスト統制が必要な案件で使用する（ユーザー・プロジェクト設定で許可リストを広げられない）。
```

- [ ] **Step 2: 13 に1行**

`docs/13-mcp-plugins-hooks.md` 13.2 の「管理者許可リスト」項目付近に追加:

```markdown
- 許可リスト（`allowedMcpServers`）に加え、明示拒否（`deniedMcpServers`）を併用する（denylist 優先）
```

- [ ] **Step 3: appendix-c C.2 に行追加**

```markdown
| MCP denylist / モデル固定 | `deniedMcpServers` / `availableModels` / `enforceAvailableModels` | ✅ | 2026-06-24 | [settings](https://code.claude.com/docs/en/settings) |
```

- [ ] **Step 4: コミット**

```bash
git add docs/11-claude-code.md docs/13-mcp-plugins-hooks.md docs/appendix-c-volatile-values.md
git commit -m "docs: note deniedMcpServers and model allowlist controls" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

### Task 6: Codex indexed web-search モード（R3 ゲート）

**Files:**
- 参照 → Modify: `docs/10-codex.md`（10.1 脚注/本文）、`docs/appendix-c-volatile-values.md`（C.1）
- 確認: `generator/agentsec/selfcheck.py`（既存の live 拒否が indexed を誤検知しないこと）

**Interfaces:**
- Consumes: 公式 config-reference の正式な値トークン。

- [ ] **Step 1: 正式トークンを一次資料で確認**

`https://developers.openai.com/codex/config-reference` で `web_search` の値モード一覧と、indexed モード（「ライブ検索を許すがページ直接取得をサーバー承認URLに限定」0.142.0/2026-06-22）の**正式トークン名**を確認する。確認できなければ ⚠️ で記載に留め、generator・selfcheck は変更しない。

- [ ] **Step 2: 10.1 に追記**

`docs/10-codex.md` 10.1 の `web_search` 段落に、確認できたトークンで1文追加（トークン未確認なら「サーバー承認URL限定のモードが追加された（要トークン確認）」と記す）。

- [ ] **Step 3: appendix-c C.1 を更新**

`web_search` のモード行に新モードを追記し、確認日を 2026-06-24 に更新（トークン未確認なら検証状態 ⚠️）。

- [ ] **Step 4: selfcheck の非誤検知を確認**

Run: `cd generator && python3 -m unittest tests.test_selfcheck -v`
Expected: PASS（selfcheck は `live` のみ拒否。indexed を生成していないため変更不要であることを確認）。

- [ ] **Step 5: コミット**

```bash
git add docs/10-codex.md docs/appendix-c-volatile-values.md
git commit -m "docs: document Codex indexed web-search mode" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

## フェーズ3: 補足（軽微な追記）

### Task 7: Claude Code 補足（Apple Events・設定ファイル保護・ドメインフロンティング）

**Files:**
- Modify: `docs/11-claude-code.md`（11.6、11.8 付近）
- Modify: `docs/appendix-c-volatile-values.md`（C.2 確認日のみ更新）

- [ ] **Step 1: 11.6 にネットワーク補足**

`docs/11-claude-code.md` 11.6 の表の後ろに追加:

```markdown
> [!NOTE]
> 組み込みプロキシは要求ホスト名で許可判定し、TLSを終端・検査しない。`github.com` のような広いドメインを許可すると、ドメインフロンティング等で許可外ホストへ到達し得る（exfiltration 経路）。脅威モデル上TLS検査が必要なら、TLS終端するカスタムプロキシ（`httpProxyPort`/`socksProxyPort`）とCA配布を用いる。`enableWeakerNetworkIsolation` は MITM プロキシ併用時の緩和であり、無条件に有効化しない。
```

- [ ] **Step 2: 11.x に Apple Events・設定ファイル保護**

`docs/11-claude-code.md` 11.8（避ける設定）付近、または 11.1 の補足として追加:

```markdown
- macOSのサンドボックスは既定でApple Eventsを遮断する。`open`・`osascript` 等のため `sandbox.allowAppleEvents` を有効化するとコード実行隔離が外れる（他アプリを無確認で起動し得る）。user/managed/CLI設定でのみ有効で、project設定からは有効化できない。
- サンドボックスは全スコープの `settings.json` と管理設定ディレクトリへの書き込みを自動的に拒否するため、サンドボックス内コマンドは自身のポリシーを書き換えられない。
```

- [ ] **Step 3: appendix-c C.2 の `allowAppleEvents` 行を確認日更新**

既存に `allowAppleEvents` が無ければ追加、あれば確認日 2026-06-24 に更新:

```markdown
| `sandbox.allowAppleEvents` | macOSのApple Events許可（既定遮断。有効化で隔離低下。project設定不可） | ✅ | 2026-06-24 | [sandboxing](https://code.claude.com/docs/en/sandboxing) |
```

- [ ] **Step 4: コミット**

```bash
git add docs/11-claude-code.md docs/appendix-c-volatile-values.md
git commit -m "docs: add Apple Events, settings-file and TLS notes" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

### Task 8: Codex 追加サーフェスの補足

**Files:**
- Modify: `docs/10-codex.md`（10.7）

- [ ] **Step 1: 10.7 に1〜2行追記**

`docs/10-codex.md` 10.7 の箇条書きに追加:

```markdown
- リモート実行は認証済みのend-to-end暗号化（Noise）リレーで行われるが、リモート実行・委譲の有効化可否は組織で審査する。
- マルチエージェント委譲は、app-server クライアントでスレッド／ターン単位に「無効・明示要求時のみ・能動」を設定できる。既定の委譲挙動を把握し、不要なら無効化する。
- rollout トークン予算（使用量追跡・上限到達でターン中断）を運用上のコスト・暴走抑止に利用できる。
```

- [ ] **Step 2: コミット**

```bash
git add docs/10-codex.md
git commit -m "docs: note Codex remote relay, delegation and token budget" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

## 仕上げ: Task 9 受入テスト追記・付録C 基準日・最終検証

**Files:**
- Modify: `docs/appendix-c-volatile-values.md`（基準確認日）
- Modify: `docs/15-acceptance-tests.md`（検証観点追加）

- [ ] **Step 1: 付録C 基準確認日を更新**

`docs/appendix-c-volatile-values.md` 冒頭の「**基準確認日**: 2026-06-20」を `2026-06-24` に更新。

- [ ] **Step 2: 15 受入テストに観点追加**

`docs/15-acceptance-tests.md` の該当箇所に追加（既存の番号体系に合わせる）:

```markdown
- `requiredMinimumVersion` を設定したとき、それ未満のクライアントで起動が拒否されること（チーム系 L3+）。
- プロジェクト設定で `denyRead:["~/"]＋allowRead:["."]` を用いた場合に、`~/.ssh` 等が読めず、プロジェクト内ファイルは読めること（堅牢パターン採用時）。
```

- [ ] **Step 3: 全テスト＋生成スモーク（複数プロファイル）**

Run:
```bash
cd generator && python3 -m unittest discover -s tests
for p in profiles/examples/*.json; do
  python3 generate.py --profile "$p" --output /tmp/gen-final && \
  python3 /tmp/gen-final/acceptance/selfcheck.py /tmp/gen-final || echo "FAIL: $p"
done
```
Expected: 全テスト PASS、各プロファイルで selfcheck exit 0。

- [ ] **Step 4: docs リンク健全性の目視確認**

変更した docs の相互リンク（`appendix-c`・`11`・`13`・`17` 等）が壊れていないことを確認。

- [ ] **Step 5: コミット**

```bash
cd /Users/a160341/Documents/_work/coding-agent-security-work
git add docs/appendix-c-volatile-values.md docs/15-acceptance-tests.md
git commit -m "docs: bump baseline date and add acceptance checks" -m "Co-authored-by: Claude <noreply@anthropic.com>"
```

---

## Self-Review（計画作成者による spec 突合）

- **2.1 資格情報ガード** → Task 2（allowRead 堅牢パターン・env scrub・sandbox.credentials⚠️）。✅
- **2.2 autoAllowBashIfSandboxed（R1）** → Task 3 Step 1 分岐。✅
- **2.3 PreToolUse hook（R1）** → Task 3 Step 1。✅
- **3.1 requiredMinimumVersion（R2）** → Task 4（profile 指定時のみ生成・既定値なし）。✅
- **3.2 deniedMcpServers / 3.3 モデル許可リスト** → Task 5（docs のみ）。✅
- **3.4 Codex indexed（R3）** → Task 6（トークン確認ゲート）。✅
- **4 フェーズ3補足** → Task 7（Claude）/ Task 8（Codex）。✅
- **5 検証方針** → Task 9（付録C 基準日・受入テスト・スモーク）。各タスク末尾にテスト/スモーク。✅
- **6 非スコープ** → deniedMcpServers/availableModels/requiredMaximumVersion/Codex 挙動は生成しない（Task 5/6 で docs のみ）。✅
- **型整合**: `build_managed_settings(..., claude_min_version=None)` の署名と orchestrate 呼び出し・テストで一貫。profile キーは `claude_min_version`（str）で一貫。✅
- **R3 注意**: Task 6 のトークン未確認時は generator/selfcheck を変更しない（誤検知防止）。✅
