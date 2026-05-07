# sync_atomgit.py —— 用Python直接上传核心文件到AtomGit
import os
import requests
import base64
import json

# AtomGit仓库信息
TOKEN = "你的AtomGit私人令牌"  # 需要在AtomGit设置里生成一个
REPO_OWNER = "gcw_lwUf3sWj"
REPO_NAME = "tianci-framework"
BRANCH = "master"

# 需要上传的文件列表（都在当前目录）
FILES = [
    "tianci_opt.cpp",
    "tianci_wormhole.py",
    "tianci_blackbox.py",
    "verify_medal.py",
    "requirements.txt",
    "README.md",
    ".github/workflows/ci.yml"
]

API_BASE = f"https://atomgit.com/api/v5/repos/{REPO_OWNER}/{REPO_NAME}/contents"

headers = {
    "Authorization": f"token {TOKEN}",
    "Content-Type": "application/json"
}

for filepath in FILES:
    if not os.path.exists(filepath):
        print(f"跳过不存在的文件: {filepath}")
        continue
    
    with open(filepath, "rb") as f:
        content = f.read()
    
    payload = {
        "message": f"sync: {filepath}",
        "content": base64.b64encode(content).decode("utf-8"),
        "branch": BRANCH
    }
    
    url = f"{API_BASE}/{filepath}"
    resp = requests.put(url, headers=headers, json=payload)
    
    if resp.status_code in [200, 201]:
        print(f"✅ {filepath}")
    else:
        print(f"❌ {filepath}: {resp.status_code} {resp.text[:100]}")

print("\n全部同步完成。")