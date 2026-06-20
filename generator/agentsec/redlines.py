"""docs/00-red-lines.md に基づく入力の整合性チェックと逸脱分類。"""

from agentsec import deviation


def check_inputs(level, plan, use_full_access, share_docker_socket,
                 network_host, direct_push):
    devs = []
    if level in ("L3", "L4") and plan == "personal":
        devs.append(deviation.make(
            "redline", "00 R3/R6",
            "L3/L4 on personal plan",
            "team plan with managed enforcement, or decline the engagement"))
    if use_full_access:
        devs.append(deviation.make(
            "redline", "00 R3",
            "bypass / danger-full-access as default",
            "regular permission mode without bypass"))
    if share_docker_socket:
        devs.append(deviation.make(
            "redline", "00 R3/09.2",
            "docker socket shared into container",
            "no docker socket mount"))
    if network_host:
        devs.append(deviation.make(
            "redline", "09.2",
            "--network host",
            "explicit egress allowlist"))
    if direct_push:
        devs.append(deviation.make(
            "redline", "00 R2/R4",
            "agent performs direct git push / deploy",
            "push and deploy via approved CI/CD only"))
    return devs


def has_blocking(deviations, override=False):
    if override:
        return False
    return any(d["type"] == "redline" for d in deviations)
