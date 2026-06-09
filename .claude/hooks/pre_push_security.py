#!/usr/bin/env python3
"""git push 전 민감 파일 포함 여부를 검사하는 Claude Code PreToolUse 훅."""
import sys
import json
import re
import subprocess

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

if not re.search(r"\bgit\s+push\b", cmd):
    sys.exit(0)

# 스테이징 + origin과 HEAD 사이 커밋된 파일 목록
staged = subprocess.run(
    ["git", "diff", "--cached", "--name-only"],
    capture_output=True, text=True
).stdout.strip()

committed = subprocess.run(
    ["git", "diff", "--name-only", "origin/main...HEAD"],
    capture_output=True, text=True
).stdout.strip()

all_files = set(filter(None, staged.split("\n") + committed.split("\n")))

DANGEROUS = [
    r"\.env(\.|$)",
    r"\.env\.(local|production|staging|development)",
    r"secrets?\.(json|yaml|yml|txt)$",
    r"credentials?\.(json|yaml|yml)$",
    r"private_?key",
    r"(id_rsa|id_ed25519|id_dsa)(\.pub)?$",
    r"\.(pem|p12|pfx|key)$",
    r"(api_?key|api_?secret|auth_?token|access_?token)\.",
    r"\.htpasswd$",
    r"jwt_?secret",
]

found = [f for f in all_files if any(re.search(p, f.lower()) for p in DANGEROUS)]

if found:
    print(json.dumps({
        "continue": False,
        "stopReason": (
            f"보안 파일 감지됨: {found}\n"
            "push가 차단됐어요. 의도된 경우라면 터미널에서 직접 `git push`를 실행하세요."
        ),
        "systemMessage": f"[보안 훅] 민감 파일 감지: {found} — push 차단됨",
    }, ensure_ascii=False))
else:
    print(json.dumps(
        {"systemMessage": "[보안 훅] 민감 파일 없음 — push 허용"},
        ensure_ascii=False
    ))
