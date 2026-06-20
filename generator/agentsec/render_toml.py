"""docs/10-codex.md の構造に限定した最小 TOML 書き込み。"""


def _needs_quoting(key):
    """Check if a TOML key needs quoting."""
    if not key:
        return True
    # Keys starting with : or containing special chars need quoting
    if key.startswith(":"):
        return True
    # Check for special characters that require quoting
    for char in key:
        if not (char.isalnum() or char in "_-"):
            return True
    return False


def _fmt_key(key):
    """Format a TOML key, quoting if necessary."""
    if _needs_quoting(key):
        return '"' + key.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return key


def _fmt_scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise TypeError(f"unsupported scalar: {type(v)}")


def _fmt_inline_table(d):
    parts = []
    for k, v in d.items():
        k_fmt = _fmt_key(k)
        if isinstance(v, list):
            if v and all(isinstance(x, dict) for x in v):
                # List of inline tables
                parts.append(f"{k_fmt} = [{', '.join(_fmt_inline_table(x) for x in v)}]")
            else:
                # List of scalars
                parts.append(f"{k_fmt} = [{', '.join(_fmt_scalar(x) for x in v)}]")
        else:
            parts.append(f"{k_fmt} = {_fmt_scalar(v)}")
    return "{" + ", ".join(parts) + "}"


def _fmt_value(v):
    if isinstance(v, list):
        if v and all(isinstance(x, dict) for x in v):
            return "[" + ", ".join(_fmt_inline_table(x) for x in v) + "]"
        return "[" + ", ".join(_fmt_scalar(x) for x in v) + "]"
    return _fmt_scalar(v)


def _emit(data, prefix, lines):
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}
    if prefix and (scalars or not tables):
        lines.append(f"[{prefix}]")
    for k, v in scalars.items():
        k_fmt = _fmt_key(k)
        lines.append(f"{k_fmt} = {_fmt_value(v)}")
    if scalars:
        lines.append("")
    for k, v in tables.items():
        # For table names in section headers, also quote if needed
        if prefix:
            new_prefix = f"{prefix}.{_fmt_key(k) if _needs_quoting(k) else k}"
        else:
            new_prefix = _fmt_key(k) if _needs_quoting(k) else k
        _emit(v, new_prefix, lines)


def dumps(data):
    lines = []
    _emit(data, "", lines)
    return "\n".join(line for line in lines).rstrip("\n") + "\n"
