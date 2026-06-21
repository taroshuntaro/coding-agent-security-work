"""生成物のレッドライン静的検査。PASS/WARN=0, FAIL=2。

docs/15-acceptance-tests.md の注意: これは静的確認に過ぎない。
実拒否は受入テストで実環境・実バージョンに対して確認すること。
"""

import sys
import json
import tomllib
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
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    text = "\n".join(line for line in lines if not line.strip().startswith("#"))
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
    for p in root.rglob("config.toml"):
        if p.parent.name == ".codex":
            _check_codex_config(p, msgs)
    for p in root.rglob("requirements.toml"):
        _check_codex_requirements(p, msgs)
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
