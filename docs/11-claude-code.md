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

`auto` はバックグラウンド安全チェック（分類器）付きのモードだが、隔離境界そのものではない。**Pro / Max / Team プランでは v2.1.228 以降、ターミナルと VS Code 拡張で起動するセッションの組み込み既定の開始モードが `auto` になった**（Enterprise プランと Console API キーは `default`。[付録C](appendix-c-volatile-values.md)）。本ガイドの推奨（L1 `plan`／L2以上 `default`）を維持するには、既定に任せず `permissions.defaultMode` を明示する。個人系では `~/.claude/settings.json` に置く（プロジェクト設定の `default`／`plan` もターミナル起動では有効だが、VS Code 拡張はプロジェクト設定を開始モードの決定に使わない）。チーム系では managed settings に置き、組織として auto mode を使わない場合は `disableAutoMode: "disable"` で選択肢から除く。auto mode を採用する場合の統制は[11.10](#1110-auto-mode分類器の位置づけと統制)を参照。

読み取り専用のレビュー用途では、コマンド実行系ツールと `WebFetch` を外し、ファイルツールを作業ディレクトリ内に限定し、`bypassPermissions` を拒否する `--restricted`（v2.1.248 以降。user / project / local の設定ファイルも無視する）も選択肢になる。

`bypassPermissions` / `--dangerously-skip-permissions` は、コンテナやVM内であっても、bind mountされたワークスペース、コンテナ内認証情報、許可されたネットワーク先へ到達できる。通常の有人開発では使用しない（[00 R3](00-red-lines.md)）。

---

## 11.3 プラン別の達成手段

### 11.3.1 個人系プラン

`managed-settings.json` による強制は利用できない。プロジェクト／ユーザー `settings.json`（[11.4](#114-プロジェクト向け-settingsjson-例)）を使うが、これは**利用者自身が解除可能**な設定である。

| 統制目標 | 個人系プランでの手段 |
|---|---|
| bypass禁止（[00 R3](00-red-lines.md)） | `settings.json` で bypass を使わない運用＋受入テスト。**強制ではなく自己規律**のため、外部境界（VM/コンテナ/ネットワーク）で実害を限定 |
| 資格情報のread遮断 | `sandbox.filesystem.denyRead` に `~/.aws`・`~/.ssh`・`~/.kube`（既定では読める点に注意）＋ホストに資格情報を置かない |
| 開始モードの固定 | `~/.claude/settings.json` の `permissions.defaultMode`（Pro/Max/Team の組み込み既定は `auto`。[11.2](#112-レベル別推奨)） |
| Bash自動承認の抑止 | `autoAllowBashIfSandboxed` は**既定が `true`**（auto-allow）のため、明示的に `false`（regular permissions mode）を設定し受入テストで確認 |
| ネットワーク限定 | `sandbox.network.allowedDomains`＋コンテナ・ホストのegress制御。許可リスト外を確認なしで拒否する `strictAllowlist: true` は **`~/.claude/settings.json`** に置く（プロジェクト設定では無効。[11.4](#114-プロジェクト向け-settingsjson-例)） |
| MCP・Hooks制限 | 利用者が自己管理。任意追加しない運用＋受入テスト |
| 監査 | 製品の組織監査ログは無い。Gitログ・プロキシログ・OS監査・コンテナログで代替 |

> 第三者（管理者）による解除不能な強制が契約上要求されるL3・L4案件は、個人系プランでは実施しない（[00 R3・R6](00-red-lines.md)）。

### 11.3.2 チーム・ビジネス系プラン

`managed-settings.json`（[11.5](#115-管理者向け-managed-settingsjson-例)）で、利用者が解除できない強制をかけられる。

| 統制目標 | チーム・ビジネス系プランでの手段 |
|---|---|
| bypass禁止 | `disableBypassPermissionsMode: "disable"`（**バージョンにより効かない実例あり。受入テスト必須**。サブエージェント定義の `permissionMode: bypassPermissions` が同キーを無視していた抜けは v2.1.223 で修正） |
| auto mode の禁止 | `disableAutoMode: "disable"`（管理設定から届くと稼働中セッションも `default` へ戻る。v2.1.251 以降。[11.10](#1110-auto-mode分類器の位置づけと統制)） |
| sandbox強制 | `sandbox.failIfUnavailable: true`（初期化失敗時に起動拒否）＋`allowUnsandboxedCommands: false`（サンドボックス外での再実行を禁止） |
| 資格情報read遮断の固定 | `sandbox.filesystem.denyRead`＋`allowManagedReadPathsOnly: true`（ユーザーがallowReadで再許可する経路を抑止） |
| ネットワーク固定 | `allowManagedDomainsOnly: true` |
| MCP・権限ルール・Hooks固定 | `allowManagedMcpServersOnly`、`allowManagedPermissionRulesOnly`、`allowManagedHooksOnly` |
| 拡張レイヤーの供給元固定 | `strictPluginOnlyCustomization`（user/project 由来のスキル・サブエージェント・Hooks・MCP を遮断）＋`strictKnownMarketplaces`（[11.9](#119-指示拡張レイヤーの統制subagentsoutput-stylesskillsrules)・[13](13-mcp-plugins-hooks.md)） |
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
      "Bash(git log *)",
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

生成ツール（`generator/`）の `settings.json` は摩擦の小さい明示列挙（`~/.ssh`・`~/.aws`・`~/.kube`）を既定とする。上記の `~/` 全遮断はより強い代替であり、案件要件に応じて手動で切り替える。また生成ツールは、選択したスタックに応じてパッケージレジストリドメイン（例: npm → `registry.npmjs.org`）を `allowedDomains` の既定として対話時に提案する（提案であり、対話中に編集できる）。

実際のビルドツールに合わせて `npm` 部分をMaven、Gradle、Python、.NETなどへ置き換える。

- `sandbox.filesystem.denyRead` は明示しない限り資格情報を読めてしまうため（[11.1の警告](#111-基本的な考え方)）、必ず指定する。
- `sandbox.network.strictAllowlist`（許可リスト外ホストを確認プロンプトなしで拒否。v2.1.219 以降）は**本例に含めていない**。このキーは user / managed / `--settings` でのみ有効で、**リポジトリの `.claude/settings.json`・`.claude/settings.local.json` に置いても無視される**（2026-09-21 確認。[付録C](appendix-c-volatile-values.md)）。個人系では各自の `~/.claude/settings.json` に `"sandbox": {"network": {"strictAllowlist": true}}` を置き、チーム系では[11.5](#115-管理者向け-managed-settingsjson-例)で固定する。生成ツールの `settings.json` も同キーを出力せず、同梱の `selfcheck.py` は project settings 内に見つけると WARN する。
- `permissions.defaultMode: "default"` は、Pro/Max/Team の組み込み既定（`auto`）をターミナル起動のセッションで上書きする（[11.2](#112-レベル別推奨)）。`auto`・`bypassPermissions` はプロジェクト設定からは効かず（v2.1.257 以降）、VS Code 拡張が開始する会話はプロジェクト設定を開始モードの決定に使わない。
- 本例は `sandbox.failIfUnavailable` を含めていない（未設定時は警告のうえ非サンドボックスで継続する fail-open。[付録C](appendix-c-volatile-values.md)）。サンドボックスを必須統制として数える案件では `"failIfUnavailable": true` を追加し、L3+ では[11.5](#115-管理者向け-managed-settingsjson-例)の managed settings で強制する（[11.8](#118-claude-codeで避ける設定運用)）。
- `autoAllowBashIfSandboxed` の**既定値は `true`**（auto-allow モード。2026-09-21 に公式 settings リファレンスで確認）。`false` にすると、sandbox内のBashコマンドもregular permission flowを通る。auto-allow でも `deny` ルールと内容指定の `ask` ルール（`Bash(git push *)` 等）は効くが、bare の `Bash` ask ルールはサンドボックス内コマンドに対して**スキップ**される。**このキーはサンドボックス自体を無効化するコマンドの自動承認によるバイパスが報告されている**（[Issue #29016](https://github.com/anthropics/claude-code/issues/29016)、closed。修正バージョンは要特定）。closed であっても挙動はバージョン依存のため、auto-allowを使う場合も受入テストで実挙動を確認する。別件の [#43713](https://github.com/anthropics/claude-code/issues/43713)（2026-09-21 時点で closed）は、シェル展開を含むコマンドが過剰にプロンプトされる挙動の報告であり、バイパスではない。環境変数 `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` を設定すると auto-allow は無効化される。
- 作業ディレクトリ外の読み取りをツール種別を問わず止めたい場合は `permissions.blockReadsOutsideWorkingDirectories: true`（v2.1.257 以降）を検討する。Read/Grep/Glob/LSP ツールによる作業ディレクトリ外の読み取りを `bypassPermissions` を含む全モードで遮断し、`cat` 等の既知の読み取りコマンドは auto mode・bypass でも確認を求める。どのスコープの `true` も有効（リポジトリ設定で有効化はできるが、解除はできない）。サンドボックス有効時はホーム配下の読み取りも拒否されるため、`~/.gitconfig` 等が必要なら `sandbox.filesystem.allowRead` で個別に再許可する。
- 資格情報の遮断は `sandbox.credentials`（`files`／`envVars` の `"mode": "deny"`。[付録C](appendix-c-volatile-values.md)）でも指定でき、公式ドキュメントは既定 read の警告とあわせてこの形を案内している。`denyRead` と同じ読み取り遮断に加え、環境変数の除去（ファイルシステム隔離を無効化しても残る）ができる。`denyRead` の**末尾スラッシュ付き指定（`~/.aws/`）は v2.1.224 未満で回避可能だった**ため、本例のようにスラッシュなしで書く。
- plan mode では auto mode が利用可能なとき分類器がコマンドを審査する（`useAutoModeDuringPlan` 既定 `true`）。L1 で都度確認を求めるなら user / local / managed 設定で `useAutoModeDuringPlan: false` を置く（`.claude/settings.json` からは解除できない）。
- Claude Codeのpermission ruleは、`deny`、`ask`、`allow`の順で評価される。広い`ask`ルールは狭い`allow`ルールより先に一致するため、たとえば`ask`へbareの`WebFetch`を置くと、`allow`の`WebFetch(domain:docs.company.example)`も自動許可されない。未一致のWeb取得を確認させたい場合は、`default` modeの通常の確認フローへ委ねる。
- より強くホーム配下全体の読み取りを遮断したい場合、**プロジェクト `settings.json` に限り** `sandbox.filesystem.denyRead` に `~/`、`sandbox.filesystem.allowRead` に `.` を指定し、ホーム全体を遮断してプロジェクトのみ再許可できる。`allowRead` の `.` は**プロジェクト設定でのみ**プロジェクトルートに解決される。`~/.claude/settings.json` や `managed-settings.json` に同じ指定を置くと `.` は `~/.claude` に解決され意図がずれるため、グローバル・管理設定では従来どおり `~/.ssh`・`~/.aws`・`~/.kube` を明示列挙する。ホーム配下のツールチェインやキャッシュ読み取りを必要とするビルドでは `~/` 全遮断が失敗の原因になり得るため、案件のビルド要件を確認してから採用する。

---

## 11.5 管理者向け `managed-settings.json` 例

**チーム・ビジネス系プラン向け。** レベル3を想定した強制設定のひな型。

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "enableArtifact": false,
  "disableArtifact": true,
  "disableRemoteControl": true,
  "disableClaudeAiConnectors": true,
  "crossSessionInbound": "refuse",
  "isolatePeerMachines": true,
  "autoMemoryEnabled": false,
  "cleanupPeriodDays": 7,
  "permissions": {
    "defaultMode": "default",
    "disableBypassPermissionsMode": "disable",
    "disableAutoMode": "disable",
    "allow": [
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
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
      "strictAllowlist": true,
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
- `disableBypassPermissionsMode` は**特定バージョンで効かなかった実例がある**（[Issue #44642](https://github.com/anthropics/claude-code/issues/44642)）。同Issueは**修正されないまま closed（not planned）**となっている（2026-08-04 確認）。設定後に[15 受入テスト](15-acceptance-tests.md)でbypassが実際に拒否されることを確認し、拒否されないバージョンでは外部境界（コンテナ・VM・ネットワーク）で代替する（[00 R5](00-red-lines.md)）。
- `enableArtifact: false` は Artifact ツール（セッション出力を claude.ai 上の Web ページとして公開する機能）を無効化する。どのスコープからも再有効化できないロックとして働く。**本例は旧キー `disableArtifact: true` を併記している**: `enableArtifact` は v2.1.196 以降でしか認識されず、それ未満のクライアントでは無効化が効かないためである。旧キーは deprecated だが `true` は引き続き同等に扱われると公式が明記しており、併記しても競合しない（`requiredMinimumVersion` で v2.1.196 以上を強制する場合は新キーのみでよい）。`disableRemoteControl`、`disableClaudeAiConnectors`、`autoMemoryEnabled`、`cleanupPeriodDays`（既定 30 日）とあわせ、組織のデータ保持・外部共有方針に合わせて調整する。
- `strictPluginOnlyCustomization`（`true`、または `["skills", "agents", "hooks", "mcp"]` の部分集合）で、user / project 由来のスキル・カスタムコマンド・サブエージェント・Hooks・MCP を遮断し、プラグイン（`strictKnownMarketplaces` で供給元を限定）と管理設定由来だけを残せる（[11.9](#119-指示拡張レイヤーの統制subagentsoutput-stylesskillsrules)・[13](13-mcp-plugins-hooks.md)）。
- 本例は他セッションからのメッセージ受信を `crossSessionInbound: "refuse"` で拒否し、他マシンの自セッションへの送信を `isolatePeerMachines: true` で承認必須にしている（[11.11](#1111-セッション間メッセージremote-controlバックグラウンドエージェント)。生成ツールも L3 以上の管理設定で同じ値を出力する）。Remote Control は `disableRemoteControl`、バックグラウンドエージェントは必要に応じて `disableAgentView` で止める。HTTP Hooks は `allowedHttpHookUrls: []` で全面遮断できる（[13](13-mcp-plugins-hooks.md)）。
- v2.1.259 以降、`allowedMcpServers` は**利用者が追加したサーバーだけ**を対象とし、`managed-mcp.json` で配布したサーバーは許可リストで絞られない。組織配布したサーバーを止めるには `deniedMcpServers` を使う（どの配布経路のサーバーにも効く）。`managedMcpServers` で HTTP/SSE サーバーを組織配布できる。
- server-managed settings（claude.ai 管理コンソールからの配信）は、取得失敗時に**既定で fail-open**（キャッシュがあればキャッシュ、無ければ管理設定なしで起動して警告）であり、`forceRemoteSettingsRefresh: true` で起動を止められる。稼働中の毎時再取得は常に fail-open。利用者が `CLAUDE_CODE_USE_BEDROCK` 等のプロバイダ変数や独自の `ANTHROPIC_BASE_URL` をシェルでエクスポートすると**取得自体がスキップ**される。公式ドキュメントも「クライアント側の統制であり、非管理端末では管理者権限なしに回避できる」と明記しているため、MDM／OS 管理パスへの配布（endpoint-managed）を基本とし、クラウドセッション向けに server-managed を併用する。
- サンドボックスを弱める、または TLS 終端・独自プロキシ・資格情報注入を伴う server-managed 設定（`tlsTerminate`・`httpProxyPort`・`sandbox.credentials` の `mask`・`filesystem.disabled`・`allowAppleEvents` 等）と Hooks は、利用者の承認ダイアログを経て初めて適用される（v2.1.251 以降。拒否すると Claude Code は終了する）。`deny` だけの `sandbox.credentials` は承認不要。
- 管理設定ファイル（`managed-settings.json`・drop-in・MDM plist・HKLM レジストリ値）が JSON として解析できない場合、v2.1.259 以降は**起動を拒否**する（以前は黙って未適用だった）。個別エントリのスキーマ違反は当該キーだけ落とされるが、`allowManagedHooksOnly`・`allowManagedMcpServersOnly` は不正値のとき `true` 扱いに倒れる。
- `requiredMinimumVersion` の目安: 2026-09-21 時点では、サブエージェント経由の bypass 抜け修正（v2.1.223）、Bash 権限チェックのバイパス修正（v2.1.223・v2.1.232・v2.1.260 等）、`blockReadsOutsideWorkingDirectories`（v2.1.257）、管理設定解析失敗時の起動拒否（v2.1.259）を含む **v2.1.259 以降**を下限にする根拠がある（[付録C](appendix-c-volatile-values.md)）。生成ツールは既定値を持たないため、profile の `claude_min_version` で明示する。
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

> [!NOTE]
> 組み込みプロキシは要求ホスト名で許可判定し、既定ではTLSを終端・検査しない。`github.com` のような広いドメインを許可すると、ドメインフロンティング等で許可外ホストへ到達し得る（exfiltration 経路）。脅威モデル上TLS検査が必要なら、TLS終端するカスタムプロキシ（`httpProxyPort`/`socksProxyPort`）とCA配布、または組み込みの `sandbox.network.tlsTerminate`（v2.1.199 以降。資格情報マスキングと併用）を用いる。`enableWeakerNetworkIsolation` は MITM プロキシ併用時の緩和であり、無条件に有効化しない。また、許可リスト外ホストを確認プロンプトなしで拒否する `sandbox.network.strictAllowlist`（v2.1.219 以降。**user / managed / `--settings` でのみ有効**）で、未許可ドメインの扱いを「確認」から「拒否」へ固定できる（[付録C](appendix-c-volatile-values.md)）。auto mode では、コマンドが必要とするホストをコマンド単位の `allowed_domains` として分類器が審査し、そのコマンドの実行中だけ開く（v2.1.271 以降）。`strictAllowlist` か `allowManagedDomainsOnly` が有効な場合、このコマンド単位の一時許可は拒否される。`tlsTerminate` も user / managed でのみ有効である。

一つの経路を止めても、別経路から同じ情報へ到達できる場合がある。機密案件では、不要なツールをdenyし、外側のネットワーク制御も適用する。

## 11.7 開発コンテナでのClaude Code

Anthropic公式ドキュメントでは、Claude Codeを開発コンテナ内にインストールすると、Claudeが実行するコマンドはホストではなくコンテナ内で実行され、bind mountされたプロジェクトへの編集はホスト側リポジトリに表示されるとしている。

推奨:

- Claude Codeをコンテナ内へインストール
- 非rootユーザーで実行
- `~/.claude` は案件単位のnamed volumeで分離
- ホストの `~/.claude`、`~/.ssh`、クラウド資格情報を共有しない
- 自動更新を採用するかバージョン固定するかを組織で決める
- 重要案件ではmanaged settingsをリポジトリ外から配布（管理パス: macOS `/Library/Application Support/ClaudeCode/`、Linux/WSL `/etc/claude-code/`、Windows `C:\Program Files\ClaudeCode\`。旧 `C:\ProgramData\ClaudeCode\` は読まれない。[付録C](appendix-c-volatile-values.md)）
- `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` を設定して資格情報の環境変数を全サブプロセスから除去する。同変数は auto-allow を無効化し、`sandbox.filesystem.disabled` を全スコープで無視させ、Linux では `!` シェルモードのコマンドもサンドボックス内で実行する
- エグレスを必要ドメインへ限定
- bypass modeは管理設定で無効化
- `~/.claude`、セッションファイル、自動メモリ、チェックポイントの保持期間と削除手順を定義
- 非対話実行で履歴を残さない必要がある場合は`--no-session-persistence`を使用（**print mode（`-p`）でのみ有効**。[付録C](appendix-c-volatile-values.md)）
- 全面的（対話モード含む）にセッションを永続化しない方針では、環境変数 `CLAUDE_CODE_SKIP_PROMPT_HISTORY` と組織運用を検討（フラグより優先される）

## 11.8 Claude Codeで避ける設定・運用

- ホスト上で `--dangerously-skip-permissions`
- bind mount・シークレット・広いネットワークを持つコンテナでbypass
- `sandbox.enabled = true` だけでサンドボックスが統制として効いていると判断する（未設定の `failIfUnavailable` は起動失敗時に非サンドボックスへフォールバックする。必須統制とする場合は `true` を併用する。[11.4の注記](#114-プロジェクト向け-settingsjson-例)）
- `excludedCommands` へ広いコマンドを登録する（管理側ロックがなく、利用者が追記して広げられる。v2.1.277 未満では複合コマンドの一部が一致するだけで全体がサンドボックス外で実行された）
- `strictAllowlist`・`tlsTerminate`・`filesystem.disabled` などをリポジトリの `.claude/settings.json` に置いて「設定した」とみなす（user / managed 設定でのみ有効）
- auto mode（分類器）を隔離境界とみなす（分類器は許可・確認ルールの後段で動く第二の判定であり、公式にも「安全を保証しない」と明記される。確実に止めたい操作は `permissions.deny`・サンドボックス・外側境界で担保する。[11.10](#1110-auto-mode分類器の位置づけと統制)）
- Dockerソケットを許可して隔離済みと判断する
- ユーザー・プロジェクトが任意のMCP、Hooks、permission allowを追加できる
- `.env` denyだけで、PythonやNodeなどの間接読み取りまで防げると判断する
- エージェントに直接push・deploy・本番操作させる
- macOSで `sandbox.allowAppleEvents` を安易に有効化する（既定でApple Eventsを遮断している。`open`・`osascript` 等のため有効化するとコード実行隔離が外れ、他アプリを無確認で起動し得る。user/managed/CLI設定でのみ有効で、project設定からは有効化できない）
- `sandbox.filesystem.disabled` を機密案件で安易に有効化する（v2.1.216 以降に存在。ネットワーク制御を残したままファイルシステム隔離だけを外す設定であり、資格情報・ワークスペース外への読み書き制限が効かなくなる）

Claude CodeのRead/Edit denyは有用だが、任意のサブプロセスが独自にファイルを開くケースまで完全に防ぐには、OSレベルのsandbox filesystem制御や外側のコンテナ・VM境界が必要である。なお、サンドボックスは全スコープの `settings.json` と管理設定ディレクトリへの書き込みを自動的に拒否するため、サンドボックス内コマンドは自身のポリシーを書き換えられない。

---

## 11.9 指示・拡張レイヤーの統制（Subagents・Output Styles・Skills・Rules）

permission・sandbox・MCP/Hooks（[13](13-mcp-plugins-hooks.md)）に加え、Claude Codeはプロジェクト指示やスキル、サブエージェント、出力スタイルでも挙動が変わる（[2.7](02-terms-and-control-layers.md)）。これらは**隔離境界ではなく指示レイヤー**であり、有効/無効や許可リストを切る管理設定キーが**揃っていないものが多い**（[付録C](appendix-c-volatile-values.md)）。確実な禁止は権限deny・サンドボックス・Hookで担保し、指示レイヤーは「リポジトリ由来として信頼前にレビュー」を基本とする。

| レイヤー | 製品側の管理キー | 推奨する統制 |
|---|---|---|
| **サブエージェント**（`.claude/agents/`） | `strictPluginOnlyCustomization: ["agents"]`（user/project 由来の定義を遮断し、プラグイン・管理設定由来のみ残す。managed 限定）、`disableAgentView`（background agents・agent viewの無効化）、`disableSideloadFlags`（`--agents` 等の sideload 拒否）。定義の `permissionMode: bypassPermissions` は `disableBypassPermissionsMode` で無効化される（v2.1.223 以降）。**サブエージェント単位の許可リストはなし**（[付録C](appendix-c-volatile-values.md)） | 定義ファイルをコードレビュー対象に。permission/sandboxはセッション全体へ及ぶ前提を[15 受入テスト](15-acceptance-tests.md)で確認。無人実行ではサブエージェント経由のツール実行も外側境界（コンテナ・VM・ネットワーク）で限定する。プロジェクト定義の frontmatter Hooks はフォルダの信頼承認後にのみ実行される（v2.1.218 以降） |
| **出力スタイル**（`outputStyle` / output-styles） | 無効化・制限のキーは**なし**（[付録C](appendix-c-volatile-values.md)） | 既定システムプロンプト（安全方針含む）を全置換するcustom output styleを機密案件で使わない運用＋ファイルレビュー。組み込みスタイルで足りる範囲に留める |
| **スキル・カスタムコマンド** | `strictPluginOnlyCustomization: ["skills"]`（user/project 由来と claude.ai 同期スキルを遮断）、`disableSkillShellExecution`（インラインシェル実行の抑止）、`disableBundledSkills`（バンドルスキルの無効化）、`strictKnownMarketplaces`／`blockedMarketplaces`（プラグイン供給元の限定） | 上記キーで実行経路と供給元を絞り、許可リスト外のskill/pluginを使わない（[13](13-mcp-plugins-hooks.md)） |
| **ルール**（`.claude/rules/`、`paths:` スコープ） | 制御キーは**なし**（[付録C](appendix-c-volatile-values.md)） | CLAUDE.md肥大化の代替だが被書換のためリポジトリ由来として信頼前レビュー（[00 R6](00-red-lines.md)）。allow/ask/denyの**権限ルールとは別物**で強制ポリシーではない |
| **プロジェクト指示**（`CLAUDE.md`・`AGENTS.md`） | 組織共通の指示は managed の `claudeMd` で配布可。`CLAUDE.md` が無いプロジェクトでは `AGENTS.md` を読む（v2.1.277 以降）。サブエージェント定義の `omitClaudeMd` で user/project の指示を読ませないことも可（managed の指示は常に読む） | 所有者を明示しコードレビュー対象に。リポジトリ由来として信頼前にレビュー。`AGENTS.md` も同じ扱いにする |

> [!NOTE]
> 出力スタイルと `.claude/rules` を強制的に無効化する管理キーは無い。スキル・サブエージェント・Hooks・MCP については `strictPluginOnlyCustomization`（managed 限定）で user/project 由来の定義を一括遮断できるようになった（2026-09-21 確認）が、残るプラグイン・管理設定由来の定義は引き続き審査対象である。これらの統制は**ファイルレビュー（コードと同じ扱い）＋ permission/sandbox/外側境界**を基本とし、[15 受入テスト](15-acceptance-tests.md)で実挙動を確認する。

---

## 11.10 auto mode（分類器）の位置づけと統制

auto mode は、ツール呼び出しを分類器（別モデル）が審査し、要求範囲を超える操作・未知のインフラへの到達・敵対的コンテンツ由来と判断した操作を止めるモードである。Pro / Max / Team では組み込み既定の開始モードになっている（[11.2](#112-レベル別推奨)）。本ガイドでの位置づけは次のとおり。

- **隔離境界ではない。** 公式ドキュメントも「プロンプトを減らすが安全を保証しない」と明記する。分類器は `deny` と内容指定の `ask` ルールの**後段**で動き、`permissions.deny` は分類器にも利用者の意図にも覆されない。確実に止める操作は deny・サンドボックス・外側境界で担保する。
- 分類器は既定で作業ディレクトリと起動時の git remote だけを信頼し、それ以外への送信、`curl | bash`、本番デプロイ等を既定で遮断する。3回連続または累計20回遮断されると通常の確認に戻る（非対話 `-p` では止まらず次へ進む）。作業ディレクトリ内の読み取りと編集は分類器を通らず自動承認される。
- 分類器の設定（`autoMode.environment` / `allow` / `soft_deny` / `hard_deny`、`autoMode.classifyAllShell`）は **user・managed・`--settings` からのみ**読み、リポジトリの `.claude/settings.json`・`.claude/settings.local.json` は読まない（v2.1.207 以降）。利用者は組織の `soft_deny` を自分の `allow` で上書きできる（加算であり、硬い境界ではない）。`hard_deny` は上書きできない。
- 組織として採用する場合は、managed settings の `autoMode.environment` に信頼するリポジトリ・レジストリ・内部ドメインを記述し、`autoMode.classifyAllShell: true` で狭い `Bash(...)` allow ルールも分類器を通す。採用しない場合は `disableAutoMode: "disable"` で選択肢から外す（[11.5](#115-管理者向け-managed-settingsjson-例)）。
- Enterprise プラン・API 利用・Bedrock/Vertex/Foundry では分類器がサーバー側で実行される（v2.1.278 以降既定）。分類器の判定理由は転写に残るが監査ログではないため、拒否を記録する必要があれば `PermissionDenied` Hook を使う。
- 本ガイドの推奨開始モードは引き続き L1 `plan`・L2以上 `default`（[11.2](#112-レベル別推奨)）。auto mode は L1〜L2 で、サンドボックス・コンテナ・ネットワーク許可リストと併用する場合に限り採用を検討する。L3以上では管理設定で `disableAutoMode` を明示するか、採用理由と分類器設定をポリシーシート（[付録A](appendix-a-policy-template.md)）に記録する。

## 11.11 セッション間メッセージ・Remote Control・バックグラウンドエージェント

v2.1.224 以降、Claude Code のセッション同士は `SendMessage` / `ListAgents` で（同一マシン間、および Remote Control を介して他マシン間で）メッセージを交換できる。Remote Control は claude.ai・モバイルアプリからローカルセッションを操作する経路である。いずれも新しい**指示注入・横展開の経路**として扱う。

| 経路 | 製品側の管理キー | 推奨 |
|---|---|---|
| セッション間メッセージの受信 | `crossSessionInbound`（`accept` / `hold` / `refuse`。project/local はより厳しい値のみ有効。managed の不正値は `refuse` 扱い） | 機密案件では managed で `refuse`、それ以外でも `hold` を既定にする。bypass で稼働中のセッション宛は既定で保留される |
| 他マシンへの送信 | `isolatePeerMachines: true`（どのスコープの `true` も有効。bypass でも承認を求める） | 有効化する |
| Remote Control | `disableRemoteControl: true`。Team/Enterprise は管理コンソールで組織単位に無効化可。リポジトリ設定からは自動起動を有効化できない（v2.1.222 以降） | L3以上は無効化。使う場合は接続中の転写が Anthropic 側に保存される点を審査する |
| バックグラウンドエージェント（`claude agents`・`--bg`） | `disableAgentView: true` | 無人実行を組織で採用していない場合は無効化 |
| auto mode 下の送信 | 分類器が `SendMessage` の内容も審査（v2.1.222 以降） | 隔離境界ではない点は[11.10](#1110-auto-mode分類器の位置づけと統制)と同じ |

[← 目次へ戻る](README.md) ｜ [次：12 CodexとClaude Codeの対応関係 →](12-product-mapping.md)
