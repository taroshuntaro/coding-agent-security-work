"""docs/10-codex.md の構造に限定した最小 TOML 書き込み。"""


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
        if isinstance(v, list):
            if v and all(isinstance(x, dict) for x in v):
                # List of inline tables
                parts.append(f"{k} = [{', '.join(_fmt_inline_table(x) for x in v)}]")
            else:
                # List of scalars
                parts.append(f"{k} = [{', '.join(_fmt_scalar(x) for x in v)}]")
        else:
            parts.append(f"{k} = {_fmt_scalar(v)}")
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
        lines.append(f"{k} = {_fmt_value(v)}")
    if scalars:
        lines.append("")
    for k, v in tables.items():
        new_prefix = f"{prefix}.{k}" if prefix else k
        _emit(v, new_prefix, lines)


def dumps(data):
    lines = []
    _emit(data, "", lines)
    return "\n".join(line for line in lines).rstrip("\n") + "\n"
