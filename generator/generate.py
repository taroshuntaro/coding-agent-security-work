"""対話 / --profile 再生で設定一式を生成する CLI。

純ロジックは agentsec 側にあり、ここは I/O 配線に徹する。input/print は
引数で注入可能にしてテストできるようにする。
"""

import argparse
import sys
from datetime import date

from agentsec import (rules, redlines, orchestrate, questions, summary, stacks,
                      detect, profile as profile_mod)


def ask_question(q, input_fn=input, print_fn=print):
    while True:
        raw = input_fn(questions.render_prompt(q))
        status, value = questions.resolve_answer(q, raw)
        if status == "help":
            print_fn(f"  {q['detail']}")
            continue
        if status == "error":
            print_fn(f"  {value}")
            continue
        return value


def confirm(prompt, input_fn=input, default=True):
    suffix = " [Y/n]: " if default else " [y/N]: "
    raw = input_fn(prompt + suffix).strip().lower()
    if raw == "":
        return default
    return raw == "y"


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


def collect_interactive(input_fn=input, print_fn=print, target_dir=".",
                        base_image_override=None):
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
    base_image = _resolve_base_image(
        a["stacks"], a["use_container"], base_image_override, input_fn, print_fn)
    return {
        "products": products, "level": a["level"], "plan": a["plan"],
        "stacks": a["stacks"], "allowed_domains": a["allowed_domains"],
        "extra_deny_paths": a["extra_deny_paths"], "use_container": a["use_container"],
        "use_full_access": a["use_full_access"],
        "share_docker_socket": a["share_docker_socket"],
        "network_host": a["network_host"], "direct_push": a["direct_push"],
        "base_image": base_image,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile")
    parser.add_argument("--output", default="./generated")
    parser.add_argument("--base-image", default=None)
    parser.add_argument("--allow-redline-override", action="store_true")
    parser.add_argument("--approver", default="")
    parser.add_argument("--save-profile")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--target-dir", default=".")
    args = parser.parse_args(argv)

    if args.profile:
        profile = profile_mod.load(args.profile)
    else:
        profile = collect_interactive(target_dir=args.target_dir,
                                      base_image_override=args.base_image)
        print(summary.format_summary(profile))
        if not confirm("この内容で生成しますか"):
            print("中止しました。")
            return 1

    if args.save_profile:
        profile_mod.save(args.save_profile, profile)
        print(f"プロファイルを保存しました: {args.save_profile}")

    if orchestrate.output_has_files(args.output) and not args.force:
        if args.profile:
            print(f"出力先 {args.output} は空ではありません。"
                  f"上書きするには --force を指定してください。")
            return 2
        if not confirm(f"出力先 {args.output} は空ではありません。上書きしますか",
                       default=False):
            print("中止しました。")
            return 1

    devs = redlines.check_inputs(
        profile["level"], profile["plan"],
        use_full_access=profile.get("use_full_access", False),
        share_docker_socket=profile.get("share_docker_socket", False),
        network_host=profile.get("network_host", False),
        direct_push=profile.get("direct_push", False))
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

    base_image = (args.base_image or profile.get("base_image")
                  or detect.DEFAULT_BASE_IMAGE)
    files = orchestrate.generate(profile, args.output, devs, base_image)
    print(f"{len(files)} 件を {args.output} に生成しました。")
    print("検証: python3 acceptance/selfcheck.py", args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
