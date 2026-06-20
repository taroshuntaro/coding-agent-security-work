"""ビルド/言語スタックを allow/ask のコマンド集合へマッピングする。"""

STACKS = {
    "npm": {
        "allow": ["Bash(npm run lint)", "Bash(npm run test *)", "Bash(npm run build *)"],
        "ask": ["Bash(npm install *)"],
    },
    "maven": {
        "allow": ["Bash(mvn test *)", "Bash(mvn compile *)"],
        "ask": ["Bash(mvn install *)"],
    },
    "gradle": {
        "allow": ["Bash(gradle test *)", "Bash(gradle build *)"],
        "ask": ["Bash(gradle publish *)"],
    },
    "pip": {
        "allow": ["Bash(pytest *)", "Bash(python -m pytest *)"],
        "ask": ["Bash(pip install *)", "Bash(poetry install *)"],
    },
    "dotnet": {
        "allow": ["Bash(dotnet test *)", "Bash(dotnet build *)"],
        "ask": ["Bash(dotnet restore *)"],
    },
    "go": {
        "allow": ["Bash(go test *)", "Bash(go build *)"],
        "ask": ["Bash(go install *)"],
    },
}


def commands_for(stack_keys):
    allow, ask = set(), set()
    for key in stack_keys:
        if key not in STACKS:
            raise ValueError(f"unknown stack: {key}")
        allow.update(STACKS[key]["allow"])
        ask.update(STACKS[key]["ask"])
    return {"allow": sorted(allow), "ask": sorted(ask)}
