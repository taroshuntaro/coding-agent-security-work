# 10 Codexの推奨方針

[← 目次へ戻る](README.md)

> [!NOTE]
> 設定キー・既定値・バージョン番号は変動する。本章の具体値は[付録C](appendix-c-volatile-values.md)に確認日付きで集約している。適用前に対象バージョンの公式ドキュメントで構文と実効性を確認すること。

## 10.1 基本的な考え方

Codex CLI・IDE連携では、サンドボックス、承認ポリシー、Web検索、サンドボックス内コマンドのネットワークアクセスを分けて管理する。

OpenAI公式ドキュメントでは、ローカルクライアントの既定の考え方として、ネットワークなし・アクティブなワークスペースへの書き込み限定が示されている。近年のバージョンでは、組み込みの `:read-only`、`:workspace`、`:danger-full-access` とカスタムpermission profileを利用できる。

`web_search` は `disabled` / `cached` / `live` の3モードを取る（旧来のboolean形式も併存）。既定は `cached`（OpenAI管理インデックスを使い、ライブ取得しない）。full accessサンドボックス利用時は `live` に既定が変化するため、業務既定値として `cached` または `disabled` を明示する。[^ws]

[^ws]: `web_search` のモードと既定値の確認日・出典は[付録C](appendix-c-volatile-values.md)を参照。`cached`/`live` の3値モードはCodex固有であり、Claude Codeには対応概念がない。 なお、ライブ検索でページ直接取得をサーバー承認URLに限定する機能が告知されているが（Codex 0.142.0）、公式 config-reference 上は `web_search` の値トークンとして公開されておらず（`disabled`/`cached`/`live` のまま、2026-06-24 確認）、業務既定値の選択肢には加えない。

## 10.2 レベル別推奨

| レベル | Codex推奨 |
|---|---|
| L1 | `:read-only`、`approval_policy = "on-request"`、`web_search = "cached"`または`disabled` |
| L2 | カスタムprofileでworkspace write、ワークスペース外deny、`.env` deny、コマンドネットワーク無効 |
| L3 | 管理requirementsでprofileを限定、full accessを禁止、live検索を禁止または例外制、MCPを許可リスト化 |
| L4 | 専用VM等でL3設定を強制。ネットワークdeny by default。クラウド利用は契約・データ処理審査後のみ |

---

## 10.3 プラン別の達成手段

統制目標はレベルで決まる（[05](05-levels.md)）。ここでは、その目標を**どの手段で達成するか**をプラン別に示す（[README「軸1：契約プラン」](README.md)）。

### 10.3.1 個人系プラン

管理 `requirements.toml` は利用できない。次の `config.toml`（[10.4](#104-開発者向け-configtoml-例)）を使うが、これは**利用者自身が解除可能**な設定である。上位レベル（L3相当）では、製品内設定に依存せず外部境界で固定する。

| 統制目標 | 個人系プランでの手段 |
|---|---|
| full access禁止（[00 R3](00-red-lines.md)） | `config.toml` で `:danger-full-access` を使わない運用＋受入テスト。**強制ではなく自己規律**のため、外部境界（VM/コンテナ/ネットワーク）で実害を限定 |
| `.env`・資格情報のread遮断 | `config.toml` の filesystem deny＋コンテナの `denyRead` 相当＋ホストに資格情報を置かない |
| ネットワーク限定 | `config.toml` の network domains 許可リスト＋コンテナ・ホストのegress制御 |
| MCP制限 | 利用者が許可リストを自己管理。任意追加しない運用＋受入テスト |
| 監査 | 製品の組織監査ログは無い。Gitログ・プロキシログ・OS監査・コンテナログで代替 |

> 第三者（管理者）による解除不能な強制が契約上要求されるL3・L4案件は、個人系プランでは実施しない（[00 R3・R6](00-red-lines.md)）。

### 10.3.2 チーム・ビジネス系プラン

管理 `requirements.toml`（[10.5](#105-管理者向け-requirementstoml-例)）で、利用者が解除できない強制をかけられる。

| 統制目標 | チーム・ビジネス系プランでの手段 |
|---|---|
| full access禁止 | `allowed_permission_profiles` から `:danger-full-access` を除外、`allowed_approval_policies` を限定 |
| live検索禁止 | `allowed_web_search_modes = ["cached"]`（`disabled` は常に許可） |
| `.env`・資格情報のread遮断 | 管理 `[permissions.filesystem].deny_read` を全profileへ強制 |
| MCP・Hooks制限 | MCP identity allowlist、`allow_managed_hooks_only` |
| 監査 | 組織アカウントの監査ログ＋設定変更・外部ツール呼び出しの監視 |

> [!CAUTION]
> クラウド配信型のmanaged requirementsは、端末に有効なキャッシュがなく取得にも失敗した場合、**管理要件なしで起動を継続する（fail-open）**仕様が公式ドキュメントに記載されている。L3・L4で強制力が必要な場合は、クラウド管理だけに依存せず、端末・コンテナ・VM上のシステム管理ファイル、MDM、ネットワーク制御、実行ラッパーを併用し、適用確認に失敗した端末を利用させない（[00 R5](00-red-lines.md)、[15 受入テスト](15-acceptance-tests.md)）。

---

## 10.4 開発者向け `config.toml` 例

以下はレベル2のひな型である（個人系・チーム・ビジネス系の両方で利用可。チーム・ビジネス系ではこれに加えて[10.5](#105-管理者向け-requirementstoml-例)で強制する）。利用するCodexバージョンで設定仕様を確認すること。

```toml
# ~/.codex/config.toml
approval_policy = "on-request"
web_search = "cached"
default_permissions = "business-workspace"

[permissions.business-workspace]
description = "Workspace editing with no command network access"
extends = ":workspace"

[permissions.business-workspace.filesystem]
# 一般的な開発ツールが必要とする最小限のOSパスだけ読み取り可能
":root" = "deny"
":minimal" = "read"

# Linux、WSL、Windowsで無制限の ** globを使用する場合の事前走査深度。
# 実際のリポジトリ階層に合わせて調整する（最低1）。
glob_scan_max_depth = 4

[permissions.business-workspace.filesystem.":workspace_roots"]
# extends = ":workspace" によりワークスペースは書き込み可能。
# :workspaceが保護する.git、.codex等に加え、案件固有の機密パスを拒否する。
"**/.env" = "deny"
"**/.env.*" = "deny"
"**/secrets/**" = "deny"
".devcontainer" = "read"

[permissions.business-workspace.network]
# Codex本体のモデル通信ではなく、サンドボックス内コマンドのネットワーク
enabled = false
```

ネットワークが必要な場合は、全許可ではなくドメイン許可リストを定義する。

```toml
[permissions.business-workspace.network]
enabled = true

[permissions.business-workspace.network.domains]
"github.com" = "allow"
"objects.githubusercontent.com" = "allow"
"registry.company.example" = "allow"
"tracking.example" = "deny"
```

許可ドメインはプロジェクトの依存取得、Git、社内ミラーなどに限定し、`"*"` の全許可を標準にしない。

---

## 10.5 管理者向け `requirements.toml` 例

**チーム・ビジネス系プラン向け。** permission profileの許可リストを管理要件として使用できる。管理対象クライアントの全台が対応バージョン以上であることを確認してから展開する（対応バージョンは[付録C](appendix-c-volatile-values.md)）。

```toml
# 組織管理 requirements.toml の例
allowed_approval_policies = ["untrusted", "on-request"]

# disabledは常に許可される。live検索を業務既定値として許可しない。
allowed_web_search_modes = ["cached"]

# リモート操作、Appshots、非管理Hooksを使用しない組織の例
allow_remote_control = false
allow_appshots = false
allow_managed_hooks_only = true

default_permissions = "org-workspace"

[allowed_permission_profiles]
":read-only" = true
org-workspace = true
# :workspace と :danger-full-access は意図的に省略

# すべてのpermission profileへ追加され、利用者が緩和できないread deny。
[permissions.filesystem]
deny_read = [
  "**/.env",
  "**/.env.*",
  "**/secrets/**",
  "~/.ssh",
  "~/.aws",
  "~/.kube",
]

[permissions.org-workspace]
description = "Managed workspace access with sensitive files denied"
extends = ":workspace"

[permissions.org-workspace.filesystem]
":root" = "deny"
":minimal" = "read"
glob_scan_max_depth = 4

[permissions.org-workspace.filesystem.":workspace_roots"]
".devcontainer" = "read"
".codex" = "read"
".git" = "read"

[permissions.org-workspace.network]
enabled = false

# 文字列パターンだけに依存せず、資格情報とネットワークでも到達不能にする。
[rules]
prefix_rules = [
  { pattern = [{ token = "git" }, { token = "push" }], decision = "forbidden", justification = "Remote repository mutation is performed outside the agent session." },
  { pattern = [{ token = "sudo" }], decision = "forbidden", justification = "Privilege escalation is not allowed." },
  { pattern = [{ token = "terraform" }, { any_of = ["apply", "destroy"] }], decision = "forbidden", justification = "Infrastructure changes require an approved pipeline." },
]
```

旧方式の `sandbox_mode` を使用するクライアントでは、少なくとも次を制約する。

```toml
allowed_approval_policies = ["untrusted", "on-request"]
allowed_sandbox_modes = ["read-only", "workspace-write"]
```

`danger-full-access` と承認なしの組み合わせを業務標準にしない。

---

## 10.6 Codex webのクラウド環境を使用する場合

Codex webのタスク環境はローカルホストとは分離されたコンテナで実行されるが、リポジトリ、設定、ネットワーク、シークレット、外部連携の審査は必要である。

公式仕様上、Codex webの環境変数はセットアップとエージェント実行中の両方で利用される。一方、Secretsはセットアップスクリプトでのみ利用でき、エージェントフェーズ開始前に削除される。

推奨:

- プライベートパッケージ取得用トークンなど、セットアップだけに必要な値はSecretsへ登録
- セットアップスクリプトが `.npmrc`、キャッシュ、ログへ値を残さないようにする
- エージェントフェーズのインターネットアクセスは原則無効
- 必要な場合はドメインとHTTPメソッドを限定
- リポジトリ接続範囲を最小化
- 組織契約、データ保持、リージョン、監査条件を確認
- 環境キャッシュに認証情報や顧客データを書き残さない
- 環境キャッシュの保持時間と、Business / Enterpriseでの共有有無は[付録C](appendix-c-volatile-values.md)で確認し、共有され得る前提で設計する
- setup用Secretを使用した後、`.npmrc`、`.pypirc`、Git credential helper、シェル履歴、ビルド成果物へ値が残っていないことを確認する

## 10.7 Codexの履歴・追加サーフェス

- ローカルのセッション履歴を保存しない要件がある場合、対応バージョンで `history.persistence = "none"` を検討する（[付録C](appendix-c-volatile-values.md)）。
- Appshots、Remote Control、Computer Use、Browser Use、Apps、MCP、Hooksは、ローカルコマンドのpermission profileとは別の制御面として審査する。
- managed requirementsの`[features]`、Apps要件、MCP identity allowlist、managed Hooksを必要に応じて使用する。
- Codexの承認によるsandbox escalationは、通常のプロファイル内操作とは異なる実行経路である。承認を「一時的な境界解除」として扱い、内容を理解せず恒久許可しない。

## 10.8 Codexで避ける設定・運用

- `:danger-full-access` を通常利用する
- `approval_policy = "never"` を業務既定値にする
- full access相当のショートカットを利用する
- live Web検索と広いローカル権限と本番シークレットを同時に許可する
- プロジェクトの `.codex` 設定を無条件に信頼する
- ユーザーが任意のMCPサーバーを追加できる
- 管理要件の取得失敗時の挙動を確認せず、クラウド管理だけに依存する
- エージェントに直接push・deploy・本番操作させる

[← 目次へ戻る](README.md) ｜ [次：11 Claude Codeの推奨方針 →](11-claude-code.md)
