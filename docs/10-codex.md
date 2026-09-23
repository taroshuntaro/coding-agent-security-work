# 10 Codexの推奨方針

[← 目次へ戻る](README.md)

> [!NOTE]
> 設定キー・既定値・バージョン番号は変動する。本章の具体値は[付録C](appendix-c-volatile-values.md)に確認日付きで集約している。適用前に対象バージョンの公式ドキュメントで構文と実効性を確認すること。

## 10.1 基本的な考え方

Codex CLI・IDE連携では、サンドボックス、承認ポリシー、Web検索、サンドボックス内コマンドのネットワークアクセスを分けて管理する。

OpenAI公式ドキュメントでは、ローカルクライアントの既定の考え方として、ネットワークなし・アクティブなワークスペースへの書き込み限定が示されている。近年のバージョンでは、組み込みの `:read-only`、`:workspace`、`:danger-full-access` とカスタムpermission profileを利用できる。

`web_search` は `disabled` / `cached` / `indexed` / `live` の4モードを取る（旧来のboolean形式も併存）。既定は `cached`（OpenAI管理インデックスを使い、外部Webへ出ない）。`indexed` は検索インデックスが承認したURLに限って外部取得を許すライブ検索、`live` は無制限のライブ取得である。full accessサンドボックス利用時は既定が `live` に変化するため、業務既定値として `cached` または `disabled` を明示する。[^ws]

[^ws]: `web_search` のモードと既定値の確認日・出典は[付録C](appendix-c-volatile-values.md)を参照。多値モードはCodex固有であり、Claude Codeには対応概念がない。0.142.0 で告知されたサーバー承認URL限定検索は、その後 `indexed` として config-reference に公開された（2026-08-04 確認）。`indexed` は `live` より狭いが外部アクセスを伴うため、業務既定値には引き続き `cached`／`disabled` を推奨し、`indexed` の採用は接続先統制を審査のうえ判断する。

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
| ネットワーク限定 | `config.toml` の network domains 許可リスト＋`features.network_proxy = true`（無いと許可リストが適用されない。[10.4](#104-開発者向け-configtoml-例)）＋コンテナ・ホストのegress制御 |
| MCP制限 | 利用者が許可リストを自己管理。任意追加しない運用＋受入テスト |
| 監査 | 製品の組織監査ログは無い。Gitログ・プロキシログ・OS監査・コンテナログで代替 |

> 第三者（管理者）による解除不能な強制が契約上要求されるL3・L4案件は、個人系プランでは実施しない（[00 R3・R6](00-red-lines.md)）。

### 10.3.2 チーム・ビジネス系プラン

管理 `requirements.toml`（[10.5](#105-管理者向け-requirementstoml-例)）で、利用者が解除できない強制をかけられる。

| 統制目標 | チーム・ビジネス系プランでの手段 |
|---|---|
| full access禁止 | `allowed_permission_profiles` から `:danger-full-access` を除外、`allowed_approval_policies` を限定 |
| live検索禁止 | `allowed_web_search_modes = ["cached"]`（`disabled` は常に許可） |
| ネットワーク限定 | `[experimental_network]`（`enabled = true`・`managed_allowed_domains_only = true`・管理者の `domains`）で管理側からプロキシを起動し、許可リストを強制。experimental 扱いのため対象 OS・バージョンで受入テストしてから展開（[10.5](#105-管理者向け-requirementstoml-例)） |
| 自動承認レビュー | `allowed_approvals_reviewers = ["user"]` で人間の承認に固定。採用する場合は `guardian_policy_config` で組織の審査方針を与える（[10.7](#107-codexの履歴追加サーフェス)） |
| `.env`・資格情報のread遮断 | 管理 `[permissions.filesystem].deny_read` を全profileへ強制 |
| MCP・Hooks制限 | MCP identity allowlist、`allow_managed_hooks_only` |
| 監査 | 組織アカウントの監査ログ＋設定変更・外部ツール呼び出しの監視 |

> [!CAUTION]
> クラウド配信型のmanaged requirementsの取得失敗時挙動について、公式ドキュメントの記載は「有効なキャッシュがなく取得にも失敗した場合はエラーとし、管理要件なしで黙って起動しない（fail-closed方向）」へ更新されている（2026-08-04 確認。以前は fail-open と記載されていた。[付録C](appendix-c-volatile-values.md)）。ただし記載変更の適用バージョンは未確認であり、実挙動はバージョン依存である。L3・L4で強制力が必要な場合は、クラウド管理だけに依存せず、端末・コンテナ・VM上のシステム管理ファイル、MDM、ネットワーク制御、実行ラッパーを併用し、**取得失敗時の実挙動を受入テストで確認**して、適用確認に失敗した端末を利用させない（[00 R5](00-red-lines.md)、[15 受入テスト](15-acceptance-tests.md)）。

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

ネットワークが必要な場合は、全許可ではなくドメイン許可リストを定義する。**`network.enabled = true` はネットワークを開くだけでプロキシを起動しない**ため、ドメイン許可リストを強制するには `features.network_proxy = true` を必ず併せて設定する。

```toml
[features]
network_proxy = true

[permissions.business-workspace.network]
enabled = true

[permissions.business-workspace.network.domains]
"github.com" = "allow"
"objects.githubusercontent.com" = "allow"
"registry.company.example" = "allow"
"tracking.example" = "deny"
```

公式ドキュメント上の挙動は次のとおりである（2026-09-23 確認。[付録C](appendix-c-volatile-values.md)）。

| `network.enabled` | `features.network_proxy` | 結果 |
|---|---|---|
| `false` | どちらでも | ネットワーク不可 |
| `true` | 無効（既定） | **無制限の直接通信**。ドメイン規則は適用されない |
| `true` | 有効 | プロキシ経由。ドメイン規則を適用（allow が無ければ外部宛ては遮断、deny が優先） |

プロキシはサンドボックス内コマンドの通信だけを対象とし、Web検索・Apps／コネクタ・MCP サーバー・ブラウザ／Computer Use・Codex cloud・Codex 本体の通信は対象外である。これらはそれぞれの設定（`web_search`、`mcp_servers`、`features.*` 等）で制御する。

許可ドメインはプロジェクトの依存取得、Git、社内ミラーなどに限定し、`"*"` の全許可を標準にしない。生成ツール（`generator/`）は、選択したスタックに応じてパッケージレジストリドメイン（例: npm → `registry.npmjs.org`）をこの許可リストの既定として対話時に提案する（提案であり、対話中に編集できる）。

> [!NOTE]
> filesystem の `:root`（ファイルシステムのルート）は公式の Permissions ページに記載された特殊パスで、`extends = ":workspace"` に `":root" = "deny"` と `":minimal" = "read"` を重ねる構成は公式の例と同じである（2026-09-23 確認。ほかに `:workspace_roots`・`:tmpdir`・`:slash_tmp` がある）。`:workspace` を継承すると、各ワークスペースルートの `.git`・`.agents`・`.codex` は読み取り専用に保護される。ネイティブ Windows の `unelevated` サンドボックスは一部の読み書きの切り分けを強制できず、その場合は実行を拒否する。Windows では適用後に受入テストで挙動を確認する。

---

## 10.5 管理者向け `requirements.toml` 例

**チーム・ビジネス系プラン向け。** permission profileの許可リストを管理要件として使用できる。管理対象クライアントの全台が対応バージョン以上であることを確認してから展開する（対応バージョンは[付録C](appendix-c-volatile-values.md)）。

```toml
# 組織管理 requirements.toml の例
# "untrusted" は、trust_level = "untrusted" のプロジェクトから導かれる厳格な承認を
# 許可するための値。approval_policy = "untrusted" の直接指定は廃止されている。
allowed_approval_policies = ["untrusted", "on-request"]

# disabledは常に許可される。live検索を業務既定値として許可しない。
allowed_web_search_modes = ["cached"]

# リモート操作、Appshots、非管理Hooksを使用しない組織の例
allow_remote_control = false
allow_appshots = false
allow_managed_hooks_only = true

# 自動承認レビュー（auto-review）を使わず人間の承認に固定する場合
# allowed_approvals_reviewers = ["user"]

default_permissions = "org-workspace"

[allowed_permission_profiles]
":read-only" = true
org-workspace = true
# :workspace と :danger-full-access は意図的に省略

# すべてのpermission profileへ追加され、利用者が緩和できないread deny。
# 絶対パス（glob可）か ~ 始まりで書く。./ 始まりの相対パスは不可。
[permissions.filesystem]
deny_read = [
  "/**/.env",
  "/**/.env.*",
  "/**/secrets/**",
  "~/.ssh",
  "~/.aws",
  "~/.kube",
  "~/.config/gcloud",
  "~/.azure",
  "~/.config/gh",
  "~/.git-credentials",
  "~/.netrc",
  "~/.docker/config.json",
  "~/.pypirc",
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

`deny_read` があると、Codex は full access を拒否し、read-only か workspace のサンドボックスで実行する。ただし**ネイティブ Windows では `deny_read` は直接のファイルツールにだけ効き、シェルのサブプロセスによる読み取りには効かない**。Windows 利用者には WSL2 かコンテナを使わせるか、ホストに資格情報を置かない運用で補う。

ネットワークが必要な場合は、`[permissions.org-workspace.network]` を `enabled = true`＋ドメイン許可リストへ置き換え、**管理側でプロキシを起動する `[experimental_network]` を併せて置く**。profile の `enabled = true` だけでは、利用者が `features.network_proxy` を有効にしない限り直接通信になる（[10.4](#104-開発者向け-configtoml-例)）。

```toml
[permissions.org-workspace.network]
enabled = true

[permissions.org-workspace.network.domains]
"github.com" = "allow"

# 管理側からプロキシを起動し、管理者の allow 規則だけを有効にする。
[experimental_network]
enabled = true
managed_allowed_domains_only = true

[experimental_network.domains]
"github.com" = "allow"
```

`[experimental_network]` は公式に experimental とされ、変更され得る。ネイティブ Windows の対応は限定的なので、対象 OS・バージョンで許可リスト外への通信が拒否されることを受入テストで確認してから展開する（[15](15-acceptance-tests.md)）。`enabled = true` だけではプロキシは起動せず、サンドボックスがネットワークを無効にしているときに通信を許可することもない。生成ツール（`generator/`）は、許可ドメインが指定されたとき config.toml に `features.network_proxy = true`、requirements.toml にこの `[experimental_network]` を出力する。

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
- managed requirementsの`[features]`、Apps要件、MCP identity allowlist（`[mcp_servers]`。stdio は `command`、HTTP は `url` で照合。**空テーブルで全MCP無効**）、managed Hooksを必要に応じて使用する。`identity.command` を文字列で書くと引数・`cwd`・環境変数を照合しないため、起動引数まで固定したい場合は `executable` と `args` のマッチャー表を使う。
- Codexの承認によるsandbox escalationは、通常のプロファイル内操作とは異なる実行経路である。承認を「一時的な境界解除」として扱い、内容を理解せず恒久許可しない。
- リモート実行は認証済みのend-to-end暗号化（Noise）リレーで行われるが、リモート実行・委譲の有効化可否は組織で審査する。
- マルチエージェント委譲は、app-server クライアントでスレッド／ターン単位に「無効・明示要求時のみ・能動」を設定できる。既定の委譲挙動を把握し、不要なら無効化する。
- rollout トークン予算（`features.rollout_budget`。使用量追跡・上限到達でターン中断）は、公式に「開発中・既定オフ」とされている。運用上のコスト・暴走抑止に使う場合は対象バージョンで挙動を確認する。
- **auto-review（Guardian）**: サンドボックス境界での承認要求（escalation）を、人間の代わりに別のレビュー用エージェントが審査する機能。公式には「メインエージェントは同じサンドボックス・承認ポリシー・ネットワーク／ファイルシステム制限の中で動き、変わるのは escalation を誰が審査するか」と説明され、権限を広げるものではない（Claude Code の auto mode に相当。[付録C](appendix-c-volatile-values.md)）。既定は `approvals_reviewer = "user"`（人間が承認）で、`"auto_review"` を選んだときだけ動く。審査の対象は、サンドボックス外への昇格・ブロックされた通信・書き込み可能ルート外の編集・承認が必要な MCP／App ツール呼び出しなど、もともと承認が要る操作に限られる。審査の構築・実行・解析に失敗した場合は実行せず（fail-closed）、タイムアウトでも実行しない。現行のオープンソース実装では、1ターン内で3回連続、または直近50件中10件が拒否されるとターンを中断する。`approval_policy = "never"`・full access では承認要求そのものが発生しないため審査も行われない。管理側は `allowed_approvals_reviewers`（`["user"]` で人間の承認に固定）、`features.guardian_approval`、`guardian_policy_config`（組織固有の審査方針。利用者の `[auto_review].policy` より優先）で制御できる。Guardian は**隔離境界ではなく承認の代替**であり、公式にも「決定論的なセキュリティ保証ではない」とされる。採用する場合も L3 以上では受入テストで実挙動を記録する。
- 信頼済みでない（`trust_level = "untrusted"`）プロジェクトでは、プロジェクトの `.codex/` 配下の設定・Hooks・rules を読み込まない（公式設定リファレンス）。加えて 0.150.0 以降はプロジェクト直下の `AGENTS.md` 指示も読み込まない（リリースノート。公式 docs の AGENTS.md ガイドには記載がない）。管理 deny-read が権限変更後も維持される修正（0.150.0）、`/cd` でサンドボックス制約を緩められない修正（0.151.0）、WSL サンドボックスからの Windows プロセス経由の脱出遮断（0.155.0）など、サンドボックス関連の修正が続いているため、対象バージョンの固定と更新時の再テスト（[17](17-periodic-review.md)）を前提にする。
- Hooks は非同期実行と MCP ツール呼び出しに対応した（0.148.0）。Hook 自体が新たな実行・通信経路になるため、`allow_managed_hooks_only = true`（`requirements.toml` でのみ有効）で供給元を限定する（[13](13-mcp-plugins-hooks.md)）。
- Agent Plugins・プラグインマーケットプレイス（0.146.0 以降）は、managed requirements の `[marketplaces].restrict_to_allowed_sources`・`features.plugins` で供給元を限定する（[付録C](appendix-c-volatile-values.md)）。

## 10.8 Codexで避ける設定・運用

- `:danger-full-access` を通常利用する
- `approval_policy = "never"` を業務既定値にする
- `approval_policy = "untrusted"` を設定する（廃止済みで、クライアントが起動しないことがある。厳格な承認が必要なら `trust_level = "untrusted"` を使う）
- ドメイン許可リストを書いただけで `features.network_proxy`（または管理側 `[experimental_network]`）を有効にしない
- full access相当のショートカットを利用する
- live Web検索と広いローカル権限と本番シークレットを同時に許可する
- プロジェクトの `.codex` 設定を無条件に信頼する
- ユーザーが任意のMCPサーバーを追加できる
- 管理要件の取得失敗時の挙動を確認せず、クラウド管理だけに依存する
- auto-review（Guardian）を隔離境界とみなす（承認の代替に過ぎず、サンドボックス・deny・外側境界の代わりにならない）
- エージェントに直接push・deploy・本番操作させる

[← 目次へ戻る](README.md) ｜ [次：11 Claude Codeの推奨方針 →](11-claude-code.md)
