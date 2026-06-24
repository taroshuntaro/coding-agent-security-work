# 11 Claude Codeの推奨方針

[← 目次へ戻る](README.md)

> [!NOTE]
> 設定キー・既定値・バージョン番号は変動する。本章の具体値は[付録C](appendix-c-volatile-values.md)に確認日付きで集約している。適用前に対象バージョンの公式ドキュメントで構文と実効性を確認すること。

## 11.1 基本的な考え方

Claude Codeでは、permission mode、allow/ask/denyルール、組み込みBashサンドボックス、開発コンテナ・VMを分けて設計する。

重要な点:

- Permissionは「ツール呼び出しを許可するか」を制御する。
- Sandboxは、実行されたBashコマンドのファイル・ネットワーク到達範囲を制限する。
- 組み込みBashサンドボックスだけでは、ファイルツール、MCP、Hooksなどを含む完全な無人実行の外側境界にはならない。
- 無人・権限バイパス運用では、コンテナまたはVM内にファイルツール、MCP、Hooksも含めて配置する。

> [!WARNING]
> **Bashサンドボックスの既定のread動作は、`~/.aws/credentials` や `~/.ssh/` などの資格情報ファイルを読み取れる。** 既定では読めてしまうため、`sandbox.filesystem.denyRead` にこれらを明示的に追加して初めて遮断される。「サンドボックス有効」だけでは資格情報は守られない。

## 11.2 レベル別推奨

| レベル | Claude Code推奨 |
|---|---|
| L1 | `plan`または`default`、Bash sandbox有効、機密ファイルdeny |
| L2 | `default`または限定的な`acceptEdits`、非rootコンテナ、bypass禁止、ネットワーク許可リスト |
| L3 | managed settingsでsandboxを強制し、初期化失敗時は起動拒否。MCP・権限ルールを管理者限定 |
| L4 | 専用VM・使い捨て環境。`default`または厳格な`dontAsk` allowlist。bypassは原則禁止 |

`auto` はバックグラウンド安全チェック付きのモードだが、隔離境界そのものではない。機密案件では、コンテナ・VM・サンドボックス・管理ルールと組み合わせる。

`bypassPermissions` / `--dangerously-skip-permissions` は、コンテナやVM内であっても、bind mountされたワークスペース、コンテナ内認証情報、許可されたネットワーク先へ到達できる。通常の有人開発では使用しない（[00 R3](00-red-lines.md)）。

---

## 11.3 プラン別の達成手段

### 11.3.1 個人系プラン

`managed-settings.json` による強制は利用できない。プロジェクト／ユーザー `settings.json`（[11.4](#114-プロジェクト向け-settingsjson-例)）を使うが、これは**利用者自身が解除可能**な設定である。

| 統制目標 | 個人系プランでの手段 |
|---|---|
| bypass禁止（[00 R3](00-red-lines.md)） | `settings.json` で bypass を使わない運用＋受入テスト。**強制ではなく自己規律**のため、外部境界（VM/コンテナ/ネットワーク）で実害を限定 |
| 資格情報のread遮断 | `sandbox.filesystem.denyRead` に `~/.aws`・`~/.ssh`・`~/.kube`（既定では読める点に注意）＋ホストに資格情報を置かない |
| Bash自動承認の抑止 | `autoAllowBashIfSandboxed` を `false` 相当（regular permissions mode）に設定し受入テストで確認 |
| ネットワーク限定 | `sandbox.network.allowedDomains`＋コンテナ・ホストのegress制御 |
| MCP・Hooks制限 | 利用者が自己管理。任意追加しない運用＋受入テスト |
| 監査 | 製品の組織監査ログは無い。Gitログ・プロキシログ・OS監査・コンテナログで代替 |

> 第三者（管理者）による解除不能な強制が契約上要求されるL3・L4案件は、個人系プランでは実施しない（[00 R3・R6](00-red-lines.md)）。

### 11.3.2 チーム・ビジネス系プラン

`managed-settings.json`（[11.5](#115-管理者向け-managed-settingsjson-例)）で、利用者が解除できない強制をかけられる。

| 統制目標 | チーム・ビジネス系プランでの手段 |
|---|---|
| bypass禁止 | `disableBypassPermissionsMode: "disable"`（**バージョンにより効かない実例あり。受入テスト必須**） |
| sandbox強制 | `sandbox.failIfUnavailable: true`（初期化失敗時に起動拒否） |
| 資格情報read遮断の固定 | `sandbox.filesystem.denyRead`＋`allowManagedReadPathsOnly: true`（ユーザーがallowReadで再許可する経路を抑止） |
| ネットワーク固定 | `allowManagedDomainsOnly: true` |
| MCP・権限ルール・Hooks固定 | `allowManagedMcpServersOnly`、`allowManagedPermissionRulesOnly`、`allowManagedHooksOnly` |
| 監査 | 組織アカウントの監査ログ |

---

## 11.4 プロジェクト向け `settings.json` 例

プロジェクト設定はリポジトリを書き換えられる利用者やエージェントによって変更できるため、強制ポリシーではなく補助設定として扱う（[00 R6](00-red-lines.md)）。

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "defaultMode": "default",
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "WebFetch(domain:docs.company.example)"
    ],
    "ask": [
      "Bash(npm install *)",
      "Bash(git commit *)",
      "WebSearch"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(ssh *)",
      "Bash(scp *)",
      "Bash(sudo *)",
      "Bash(kubectl *)",
      "Bash(helm *)",
      "Bash(terraform apply *)",
      "Bash(terraform destroy *)",
      "Bash(git push *)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": false,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": [
        "~/.ssh",
        "~/.aws",
        "~/.kube"
      ]
    },
    "network": {
      "allowedDomains": [
        "github.com",
        "*.npmjs.org",
        "registry.company.example"
      ]
    }
  }
}
```

生成ツール（`generator/`）の `settings.json` は摩擦の小さい明示列挙（`~/.ssh`・`~/.aws`・`~/.kube`）を既定とする。上記の `~/` 全遮断はより強い代替であり、案件要件に応じて手動で切り替える。

実際のビルドツールに合わせて `npm` 部分をMaven、Gradle、Python、.NETなどへ置き換える。

- `sandbox.filesystem.denyRead` は明示しない限り資格情報を読めてしまうため（[11.1の警告](#111-基本的な考え方)）、必ず指定する。
- `autoAllowBashIfSandboxed` を `false` にすると、sandbox内のBashコマンドもregular permission flowを通る。**このキーはサンドボックス自体を無効化するコマンドの自動承認や、シェル展開によるバイパスが報告されている**（[Issue #29016](https://github.com/anthropics/claude-code/issues/29016)、[#43713](https://github.com/anthropics/claude-code/issues/43713)）。auto-allowを使う場合も受入テストで実挙動を確認する。[Issue #29016](https://github.com/anthropics/claude-code/issues/29016) は closed である（2026-06-24 確認、修正バージョンは要特定）。closed であっても挙動はバージョン依存のため、受入テストでの確認は引き続き必須とする。
- Claude Codeのpermission ruleは、`deny`、`ask`、`allow`の順で評価される。広い`ask`ルールは狭い`allow`ルールより先に一致するため、たとえば`ask`へbareの`WebFetch`を置くと、`allow`の`WebFetch(domain:docs.company.example)`も自動許可されない。未一致のWeb取得を確認させたい場合は、`default` modeの通常の確認フローへ委ねる。
- より強くホーム配下全体の読み取りを遮断したい場合、**プロジェクト `settings.json` に限り** `sandbox.filesystem.denyRead` に `~/`、`sandbox.filesystem.allowRead` に `.` を指定し、ホーム全体を遮断してプロジェクトのみ再許可できる。`allowRead` の `.` は**プロジェクト設定でのみ**プロジェクトルートに解決される。`~/.claude/settings.json` や `managed-settings.json` に同じ指定を置くと `.` は `~/.claude` に解決され意図がずれるため、グローバル・管理設定では従来どおり `~/.ssh`・`~/.aws`・`~/.kube` を明示列挙する。ホーム配下のツールチェインやキャッシュ読み取りを必要とするビルドでは `~/` 全遮断が失敗の原因になり得るため、案件のビルド要件を確認してから採用する。

---

## 11.5 管理者向け `managed-settings.json` 例

**チーム・ビジネス系プラン向け。** レベル3を想定した強制設定のひな型。

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "disableArtifact": true,
  "disableRemoteControl": true,
  "disableClaudeAiConnectors": true,
  "autoMemoryEnabled": false,
  "cleanupPeriodDays": 7,
  "permissions": {
    "defaultMode": "default",
    "disableBypassPermissionsMode": "disable",
    "disableAutoMode": "disable",
    "allow": [
      "Bash(git status)",
      "Bash(git diff *)",
      "WebFetch(domain:docs.company.example)"
    ],
    "ask": [
      "Bash(npm run *)",
      "Bash(mvn test *)",
      "Bash(gradle test *)",
      "Bash(git commit *)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)",
      "WebSearch",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(ssh *)",
      "Bash(scp *)",
      "Bash(sudo *)",
      "Bash(kubectl *)",
      "Bash(helm *)",
      "Bash(terraform apply *)",
      "Bash(terraform destroy *)",
      "Bash(git push *)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "failIfUnavailable": true,
    "autoAllowBashIfSandboxed": false,
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "denyRead": [
        "~/.ssh",
        "~/.aws",
        "~/.kube"
      ],
      "allowManagedReadPathsOnly": true
    },
    "network": {
      "allowedDomains": [
        "github.com",
        "registry.company.example"
      ],
      "deniedDomains": [
        "production-api.company.example"
      ],
      "allowManagedDomainsOnly": true
    }
  },
  "allowedMcpServers": [],
  "allowManagedMcpServersOnly": true,
  "allowManagedPermissionRulesOnly": true,
  "allowManagedHooksOnly": true,
  "disableSkillShellExecution": true
}
```

注意:

- `allowedMcpServers` の許可リストに加え、`deniedMcpServers` で特定サーバーを明示拒否できる（denylist が優先）。
- `availableModels` と `enforceAvailableModels: true` で、利用可能モデルを許可リストへ固定できる。データ越境・コスト統制が必要な案件で使用する（ユーザー・プロジェクト設定で許可リストを広げられない）。
- すべての開発でMCPを禁止する例として `allowedMcpServers: []` を使用している。利用する場合は審査済みサーバーだけを登録する。
- `allowManagedPermissionRulesOnly` は、ユーザーやプロジェクトが独自のallow/ask/denyを追加することを防ぐため、プロジェクト固有の柔軟性と引き換えになる。
- `sandbox.network.allowedDomains` は主にsandbox内のBashコマンドの送信先を制御する。Claude Code本体の認証・推論・更新通信は、端末・コンテナ・組織プロキシ側で別途制御する。
- `WebFetch(domain:...)` はWebFetch用のpermission rule、`WebSearch`はspecifierを持たない独立ツールである。Bashの`curl`制御と混同しない。
- server-managed settingsを利用し、取得失敗時に起動を止める場合は、managed settingsへ`"forceRemoteSettingsRefresh": true`を追加する。OS/MDMで保護されたmanaged settingsの方が強い保証を持つ。
- `autoAllowBashIfSandboxed` を明示的に `false` とする。auto-allowを使うとsandbox内のBashコマンドがpermission modeにかかわらず自動承認され得る。**このキーにはバイパス実例があるため**（[11.4](#114-プロジェクト向け-settingsjson-例)）、`false`運用でも受入テストで確認する。
- `requiredMinimumVersion`（必要なら `requiredMaximumVersion`）を設定すると、許可バージョン範囲外のクライアント起動を拒否でき、「管理設定が古いクライアントで無視される」問題（[17.2](17-periodic-review.md)）を製品側で防げる。生成ツールは profile の `claude_min_version` を指定したときのみ出力する（既定値は持たない）。
- `sandbox.filesystem.allowManagedReadPathsOnly`を有効にすると、ユーザー・プロジェクト設定の`allowRead`でmanaged `denyRead`領域を再許可する経路を抑えられる。
- `disableSkillShellExecution`は、ユーザー・プロジェクト・プラグイン由来のskillsやcustom commandsに埋め込まれたインラインシェル実行を止める例である。
- `disableAutoMode`はAuto modeを組織として未承認とする例である。Auto modeを採用する場合は、research previewであることとclassifierの境界を評価して外す。
- `disableBypassPermissionsMode` は**特定バージョンで効かなかった実例がある**（[Issue #44642](https://github.com/anthropics/claude-code/issues/44642)）。設定後に[15 受入テスト](15-acceptance-tests.md)でbypassが実際に拒否されることを確認する（[00 R5](00-red-lines.md)）。
- `disableArtifact`、`disableRemoteControl`、`disableClaudeAiConnectors`、`autoMemoryEnabled`、`cleanupPeriodDays`は、組織のデータ保持・外部共有方針に合わせて調整する。
- コンテナ内のサンドボックスでは、環境によって追加依存や制約がある。テスト端末で検証してから展開する。

---

## 11.6 WebSearch、WebFetch、Bashネットワークの区別

| 経路 | 制御方法 |
|---|---|
| `WebSearch` | bareの`WebSearch` allow/ask/deny rule。ドメインspecifierは持たない |
| `WebFetch` | `WebFetch(domain:example.com)`などのpermission rule |
| BashからのHTTP通信 | `sandbox.network.allowedDomains` / `deniedDomains`、OS・プロキシ、Bashルール |
| Claude Code本体のモデル通信 | 端末・コンテナ・企業プロキシ・認証方式のネットワークポリシー |
| MCP・Hooks | MCP allowlist、Hooks管理、各プロセスのネットワーク・資格情報 |

一つの経路を止めても、別経路から同じ情報へ到達できる場合がある。機密案件では、不要なツールをdenyし、外側のネットワーク制御も適用する。

## 11.7 開発コンテナでのClaude Code

Anthropic公式ドキュメントでは、Claude Codeを開発コンテナ内にインストールすると、Claudeが実行するコマンドはホストではなくコンテナ内で実行され、bind mountされたプロジェクトへの編集はホスト側リポジトリに表示されるとしている。

推奨:

- Claude Codeをコンテナ内へインストール
- 非rootユーザーで実行
- `~/.claude` は案件単位のnamed volumeで分離
- ホストの `~/.claude`、`~/.ssh`、クラウド資格情報を共有しない
- 自動更新を採用するかバージョン固定するかを組織で決める
- 重要案件ではmanaged settingsをリポジトリ外から配布
- エグレスを必要ドメインへ限定
- bypass modeは管理設定で無効化
- `~/.claude`、セッションファイル、自動メモリ、チェックポイントの保持期間と削除手順を定義
- 非対話実行で履歴を残さない必要がある場合は`--no-session-persistence`等を使用（[付録C](appendix-c-volatile-values.md)）
- 全面的にプロンプト履歴を書き込まない方針では、対応する環境変数と組織運用を検討

## 11.8 Claude Codeで避ける設定・運用

- ホスト上で `--dangerously-skip-permissions`
- bind mount・シークレット・広いネットワークを持つコンテナでbypass
- `sandbox.enabled = true` だけ設定し、起動失敗時に非サンドボックスへフォールバックさせる（`failIfUnavailable: true` を併用する）
- `excludedCommands` へ広いコマンドを登録する
- Dockerソケットを許可して隔離済みと判断する
- ユーザー・プロジェクトが任意のMCP、Hooks、permission allowを追加できる
- `.env` denyだけで、PythonやNodeなどの間接読み取りまで防げると判断する
- エージェントに直接push・deploy・本番操作させる

Claude CodeのRead/Edit denyは有用だが、任意のサブプロセスが独自にファイルを開くケースまで完全に防ぐには、OSレベルのsandbox filesystem制御や外側のコンテナ・VM境界が必要である。

[← 目次へ戻る](README.md) ｜ [次：12 CodexとClaude Codeの対応関係 →](12-product-mapping.md)
