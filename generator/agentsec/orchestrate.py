"""入力プロファイルから全成果物を書き出す。"""

import json
from pathlib import Path

from agentsec import (rules, build_claude, build_codex, render_text,
                      profile as profile_mod)


def _write(out_root, rel, text):
    path = Path(out_root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return str(path)


def _json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _deviations_block(deviations):
    if not deviations:
        return "（なし）"
    return "\n".join(
        f"- [{d['type']}] {d['rule_ref']}: {d['chosen']} "
        f"（推奨: {d['recommended']} / 理由: {d['reason']} / 承認: {d['approver']}）"
        for d in deviations)


def generate(profile, output_dir, deviations, base_image):
    profile_mod.validate(profile)
    files = {}
    lvl, plan = profile["level"], profile["plan"]
    domains = profile["allowed_domains"]
    extra = profile["extra_deny_paths"]
    stacks_keys = profile["stacks"]

    if "claude" in profile["products"]:
        files["claude-code/.claude/settings.json"] = _write(
            output_dir, "claude-code/.claude/settings.json",
            _json(build_claude.build_settings(lvl, stacks_keys, domains, extra)))
        if plan == "team":
            files["claude-code/managed-settings.json"] = _write(
                output_dir, "claude-code/managed-settings.json",
                _json(build_claude.build_managed_settings(lvl, stacks_keys, domains, extra, [])))

    if "codex" in profile["products"]:
        files["codex/.codex/config.toml"] = _write(
            output_dir, "codex/.codex/config.toml",
            build_codex.build_config(lvl, stacks_keys, domains, extra))
        if plan == "team":
            files["codex/requirements.toml"] = _write(
                output_dir, "codex/requirements.toml",
                build_codex.build_requirements(lvl, domains, extra))

    if profile["use_container"]:
        files["Dockerfile"] = _write(output_dir, "Dockerfile",
            render_text.render("container/Dockerfile.tmpl", {"base_image": base_image}))
        files["docker-compose.yml"] = _write(output_dir, "docker-compose.yml",
            render_text.render("container/docker-compose.yml.tmpl", {"service_name": "dev"}))
        files[".devcontainer/devcontainer.json"] = _write(
            output_dir, ".devcontainer/devcontainer.json",
            render_text.render("container/devcontainer.json.tmpl", {"service_name": "dev"}))
        files[".dockerignore"] = _write(output_dir, ".dockerignore",
            render_text.render("container/dockerignore.tmpl", {}))

    text_map = {
        "level": lvl, "plan": plan, "products": ", ".join(profile["products"]),
        "use_container": str(profile["use_container"]), "base_image": base_image,
        "deny_paths": ", ".join(rules.SENSITIVE_READ_PATHS + extra),
        "allowed_domains": ", ".join(domains),
        "deviations_block": _deviations_block(deviations),
    }
    files["acceptance/checklist.md"] = _write(output_dir, "acceptance/checklist.md",
        render_text.render("acceptance/checklist.md.tmpl", text_map))
    files["POLICY-SHEET.md"] = _write(output_dir, "POLICY-SHEET.md",
        render_text.render("policy/policy-sheet.md.tmpl", text_map))
    files["README.md"] = _write(output_dir, "README.md",
        render_text.render("policy/README.md.tmpl", text_map))

    # selfcheck.py を生成物へ同梱（パッケージから読み出してコピー）
    selfcheck_src = (Path(__file__).resolve().parent / "selfcheck.py").read_text(encoding="utf-8")
    files["acceptance/selfcheck.py"] = _write(output_dir, "acceptance/selfcheck.py", selfcheck_src)

    record = profile_mod.build_record(profile, files, deviations)
    files["generation-profile.json"] = _write(output_dir, "generation-profile.json", _json(record))
    return files
