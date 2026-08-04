"""ビルド/言語スタックを allow/ask のコマンド集合へマッピングする。"""

STACKS = {
    "npm": {
        "allow": ["Bash(npm run lint)", "Bash(npm run test *)", "Bash(npm run build *)"],
        "ask": ["Bash(npm install *)"],
        "domains": ["registry.npmjs.org"],
    },
    "maven": {
        "allow": ["Bash(mvn test *)", "Bash(mvn compile *)"],
        "ask": ["Bash(mvn install *)"],
        "domains": ["repo.maven.apache.org"],
    },
    "gradle": {
        "allow": ["Bash(gradle test *)", "Bash(gradle build *)"],
        # publish はレジストリ公開＝原則拒否候補（docs/07 7.3）のため ask に置かない
        "ask": [],
        "domains": ["repo.maven.apache.org", "plugins.gradle.org"],
    },
    "pip": {
        "allow": ["Bash(pytest *)", "Bash(python -m pytest *)"],
        "ask": ["Bash(pip install *)", "Bash(poetry install *)"],
        "domains": ["pypi.org", "files.pythonhosted.org"],
    },
    "dotnet": {
        "allow": ["Bash(dotnet test *)", "Bash(dotnet build *)"],
        "ask": ["Bash(dotnet restore *)"],
        "domains": ["api.nuget.org"],
    },
    "go": {
        "allow": ["Bash(go test *)", "Bash(go build *)"],
        "ask": ["Bash(go install *)"],
        "domains": ["proxy.golang.org", "sum.golang.org"],
    },
}

KNOWN = frozenset(STACKS)


def unknown_keys(keys):
    """keys のうち STACKS に無いものを入力順で返す。"""
    return [k for k in keys if k not in STACKS]


def commands_for(stack_keys):
    allow, ask = set(), set()
    for key in stack_keys:
        if key not in STACKS:
            raise ValueError(f"unknown stack: {key}")
        allow.update(STACKS[key]["allow"])
        ask.update(STACKS[key]["ask"])
    return {"allow": sorted(allow), "ask": sorted(ask)}


def domains_for(stack_keys):
    """選択スタックのパッケージレジストリドメインを union・sorted で返す。"""
    domains = set()
    for key in stack_keys:
        if key not in STACKS:
            raise ValueError(f"unknown stack: {key}")
        domains.update(STACKS[key]["domains"])
    return sorted(domains)
