"""対話 / --profile 再生で設定一式を生成する CLI。"""

import argparse
import sys
from datetime import date

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
    if args.allow_redline_override and devs and not args.approver.strip():
        print("エラー: --allow-redline-override 使用時は --approver を指定してください。")
        return 2
    for d in devs:
        d["approver"] = args.approver
        d["date"] = date.today().isoformat()

    files = orchestrate.generate(profile, args.output, devs, args.base_image)
    print(f"{len(files)} 件を {args.output} に生成しました。")
    print("検証: python acceptance/selfcheck.py", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
