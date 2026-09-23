# 20 参照資料

[← 目次へ戻る](README.md)

> [!NOTE]
> 各リンクの内容は更新される。製品仕様に関する記述は、参照時点（[付録C](appendix-c-volatile-values.md)の確認日）の内容に基づく。

## OpenAI / Codex

> [!NOTE]
> `developers.openai.com/codex` 配下は `learn.chatgpt.com/docs` 配下へ恒久移転している（308リダイレクト。2026-08-04 確認）。以下の旧URLはリダイレクトで到達できる。

- [Sandbox – Codex](https://developers.openai.com/codex/concepts/sandboxing)
- [Agent approvals & security – Codex](https://developers.openai.com/codex/agent-approvals-security)
- [Permissions – Codex](https://developers.openai.com/codex/permissions)
- [Config basics – Codex](https://developers.openai.com/codex/config-basic)
- [Managed configuration – Codex](https://developers.openai.com/codex/enterprise/managed-configuration)
- [Cloud environments – Codex](https://developers.openai.com/codex/cloud/environments)
- [Agent internet access – Codex](https://developers.openai.com/codex/cloud/internet-access)
- [Configuration reference – Codex](https://developers.openai.com/codex/config-reference)
- [Model Context Protocol – Codex](https://developers.openai.com/codex/mcp)
- [Admin setup – Codex](https://developers.openai.com/codex/enterprise/admin-setup)
- [Auto-review – Codex](https://learn.chatgpt.com/docs/sandboxing/auto-review)
- [ChatGPT & Codex changelog](https://learn.chatgpt.com/docs/changelog)
- [Releases – openai/codex (GitHub)](https://github.com/openai/codex/releases)

## Anthropic / Claude Code

- [Security – Claude Code](https://code.claude.com/docs/en/security)
- [Configure permissions – Claude Code](https://code.claude.com/docs/en/permissions)
- [Choose a permission mode – Claude Code](https://code.claude.com/docs/en/permission-modes)
- [Configure the sandboxed Bash tool – Claude Code](https://code.claude.com/docs/en/sandboxing)
- [Choose a sandbox environment – Claude Code](https://code.claude.com/docs/en/sandbox-environments)
- [Claude Code settings](https://code.claude.com/docs/en/settings)
- [Tools reference – Claude Code](https://code.claude.com/docs/en/tools-reference)
- [Server-managed settings – Claude Code](https://code.claude.com/docs/en/server-managed-settings)
- [Development containers – Claude Code](https://code.claude.com/docs/en/devcontainer)
- [Set up Claude Code for your organization](https://code.claude.com/docs/en/admin-setup)
- [All settings（settings reference） – Claude Code](https://code.claude.com/docs/en/settings-reference)
- [Deploy managed settings – Claude Code](https://code.claude.com/docs/en/managed-settings)
- [Configure auto mode – Claude Code](https://code.claude.com/docs/en/auto-mode-config)
- [Hooks – Claude Code](https://code.claude.com/docs/en/hooks)
- [Cross-session messaging – Claude Code](https://code.claude.com/docs/en/cross-session-messaging)
- [CLI reference – Claude Code](https://code.claude.com/docs/en/cli-reference)
- [CHANGELOG – Claude Code (GitHub)](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)

## 一般的なセキュリティ指針

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [NIST SP 800-218 Secure Software Development Framework](https://csrc.nist.gov/pubs/sp/800/218/final)
- [NIST SP 800-218A Secure Software Development Practices for Generative AI and Dual-Use Foundation Models（2024-07）](https://csrc.nist.gov/pubs/sp/800/218/a/final)
- [Docker Bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)
- [CISA Secure by Design](https://www.cisa.gov/securebydesign)

## AIエージェントのセキュリティ（製品非依存）

> [!NOTE]
> 本節は2026-09-23に各一次情報で確認した。

- [OWASP Top 10 for Agentic Applications for 2026（2025-12-09）](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) — [3.3](03-risks.md)の対応表の基準
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)
- [The lethal trifecta for AI agents（Simon Willison, 2025-06-16）](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) — [3.2](03-risks.md)の3要素
- [Agents Rule of Two: A Practical Approach to AI Agent Security（Meta, 2025-10-31）](https://ai.meta.com/blog/practical-ai-agent-security/) — [3.2](03-risks.md)の3要素
- [MCP Security Best Practices（Model Context Protocol, 2026-07-28 版）](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices) — [13.4](13-mcp-plugins-hooks.md)
- [MCP Specification: Tools（2026-07-28 版）](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) — ツールの注釈を非信頼として扱う規定
- [NSA AISC: Model Context Protocol (MCP): Security Design Considerations for AI-Driven Automation（2026-05）](https://media.defense.gov/2026/Jun/02/2003943289/-1/-1/0/CSI_MCP_SECURITY.PDF)
- [We Have a Package for You! A Comprehensive Analysis of Package Hallucinations by Code Generating LLMs（USENIX Security 2025）](https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen) — [7.4](07-command-policy.md)
- [総務省・経済産業省「AI事業者ガイドライン（第1.2版）」（2026-03-31）](https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/pdf/20260331_1.pdf)
- [「生成AIおよびAIエージェントを安全に活用するための手引書」（2026-07）](https://www.ipa.go.jp/jinzai/ics/core_human_resource/final_project/2026/ai-security.html) — IPA 産業サイバーセキュリティセンター 中核人材育成プログラム第9期生の卒業プロジェクト成果物。IPAの著作物・公式ガイドラインではない

## 事例

- [Nx Security Advisory GHSA-cxm3-wv7p-598c（2025-08-27）](https://github.com/nrwl/nx/security/advisories/GHSA-cxm3-wv7p-598c) ・ [Nx postmortem: S1ngularity（2025-09-05）](https://nx.dev/blog/s1ngularity-postmortem) — [3.1](03-risks.md)
- [Snyk: Weaponizing AI Coding Agents for Malware in the Nx Malicious Package](https://snyk.io/blog/weaponizing-ai-coding-agents-for-malware-in-the-nx-malicious-package/) ・ [Wiz: s1ngularity supply chain attack](https://www.wiz.io/blog/s1ngularity-supply-chain-attack) — エージェントCLIの起動方法・標的の解析（セキュリティ企業による二次情報）

## CI・依存パッケージ

- [GitHub Actions: Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use) ・ [Securely using pull_request_target](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target) — [14.4](14-git-cicd.md)
- [anthropics/claude-code-action: Security](https://github.com/anthropics/claude-code-action/blob/main/docs/security.md) ・ [openai/codex-action: Security](https://github.com/openai/codex-action/blob/main/docs/security.md) — [14.4](14-git-cicd.md)
- クールダウン設定（[7.4](07-command-policy.md)）: [npm config](https://docs.npmjs.com/cli/v11/using-npm/config) ・ [pnpm settings](https://pnpm.io/settings/dependency-resolution) ・ [Yarn .yarnrc.yml](https://yarnpkg.com/configuration/yarnrc) ・ [Bun bunfig.toml](https://bun.com/docs/runtime/bunfig) ・ [uv settings](https://docs.astral.sh/uv/reference/settings/) ・ [pip install](https://pip.pypa.io/en/stable/cli/pip_install/)

[← 目次へ戻る](README.md) ｜ [付録A 案件別ポリシー記入テンプレート →](appendix-a-policy-template.md)
