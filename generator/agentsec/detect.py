"""対象ディレクトリのマーカーファイルからビルド/言語スタックを検出する純ロジック。

ファイルシステム読み取りのみを行い、対話 I/O は持たない（generate.py 側に置く）。

スタックを増やすときの編集箇所:
  1. agentsec/stacks.py の STACKS（allow/ask コマンド。これが正典）
  2. このファイルの MARKERS（マーカー → スタックキー）
  3. （任意）このファイルの BASE_IMAGES（スタックキー → base-image）
MARKERS の値と BASE_IMAGES のキーは stacks.KNOWN の部分集合でなければならない
（tests/test_detect.py の整合テストで強制）。
"""

import os
from pathlib import Path

# マーカー（ファイル名 or "*.ext" グロブ） → 既知スタックキー（stacks.STACKS と一致）
MARKERS = {
    "package.json": "npm",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "pyproject.toml": "pip",
    "requirements.txt": "pip",
    "setup.py": "pip",
    "Pipfile": "pip",
    "go.mod": "go",
    "*.csproj": "dotnet",
}

# 未対応スタックのマーカー → 表示ラベル（警告に使う。生成はしない）
UNSUPPORTED_MARKERS = {
    "Cargo.toml": "rust",
    "Gemfile": "ruby",
    "composer.json": "php",
}

# 走査時に降りない依存/VCS/成果物ディレクトリ（誤検出と無駄走査を防ぐ）
IGNORE_DIRS = {
    ".git", "node_modules", "vendor", ".venv", "venv", "__pycache__",
    "dist", "build", "target", ".gradle", "bin", "obj", ".next", ".tox",
}

MAX_DEPTH = 3


def _file_matches(filenames, marker):
    if marker.startswith("*."):
        suffix = marker[1:]
        return any(name.endswith(suffix) for name in filenames)
    return marker in filenames


def detect_stacks(target_dir, max_depth=MAX_DEPTH):
    """target_dir 配下を max_depth まで再帰走査し検出スタックの union を返す。

    IGNORE_DIRS と隠しディレクトリ（先頭ドット）は降りない。
    返り値: {"known": [...], "unsupported": [...]}（ともにソート済み・重複なし）。
    ディレクトリが無い場合は空リストを返す。
    """
    root = Path(target_dir)
    if not root.is_dir():
        return {"known": [], "unsupported": []}
    known, unsupported = set(), set()
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth >= max_depth:
            dirnames[:] = []  # これ以上深くは降りない
        else:
            dirnames[:] = [d for d in dirnames
                           if d not in IGNORE_DIRS and not d.startswith(".")]
        for marker, key in MARKERS.items():
            if _file_matches(filenames, marker):
                known.add(key)
        for marker, label in UNSUPPORTED_MARKERS.items():
            if marker in filenames:
                unsupported.add(label)
    return {"known": sorted(known), "unsupported": sorted(unsupported)}
