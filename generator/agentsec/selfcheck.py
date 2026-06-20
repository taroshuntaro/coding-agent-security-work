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
