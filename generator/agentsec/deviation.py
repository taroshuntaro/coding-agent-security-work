"""逸脱レジスタの1件を表すデータを生成する。"""


def make(dtype, rule_ref, chosen, recommended, reason="", approver="", date=""):
    if dtype not in ("redline", "recommendation"):
        raise ValueError(f"unknown deviation type: {dtype}")
    return {
        "type": dtype,
        "rule_ref": rule_ref,
        "chosen": chosen,
        "recommended": recommended,
        "reason": reason,
        "approver": approver,
        "date": date,
    }
