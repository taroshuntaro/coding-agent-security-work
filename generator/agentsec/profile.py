"""profile.json の読み書き・検証と generation-profile.json の記録メタ生成。"""

import json
import hashlib
from datetime import datetime, timezone

from agentsec import rules

REQUIRED_KEYS = ("products", "level", "plan", "stacks", "allowed_domains",
                 "extra_deny_paths", "use_container")


def validate(profile):
    for key in REQUIRED_KEYS:
        if key not in profile:
            raise ValueError(f"missing key: {key}")
    if profile["level"] not in rules.LEVELS:
        raise ValueError(f"invalid level: {profile['level']}")
    if profile["plan"] not in rules.PLANS:
        raise ValueError(f"invalid plan: {profile['plan']}")
    for p in profile["products"]:
        if p not in rules.PRODUCTS:
            raise ValueError(f"invalid product: {p}")


def load(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    validate(data)
    return data


def save(path, profile):
    validate(profile)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_record(profile, generated_files, deviations):
    return {
        "profile": profile,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_versions": {},  # 受入テスト時に手記入（docs/15-acceptance-tests.md 15.2）
        "files": {rel: file_sha256(path) for rel, path in generated_files.items()},
        "deviations": list(deviations),
    }
