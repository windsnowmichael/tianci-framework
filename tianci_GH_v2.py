# -*- coding: utf-8 -*-
"""
天赐范式 · GitHub IP 自动追踪与加速器
感知算子（Web 探头）自动适配最佳解析链路，修复 DoH 不可用兜底逻辑
"""
import requests
import platform
import os
import subprocess
import re
import sys

# --- 1. 配置部分 ---
GITHUB_DOMAINS = [
    "github.com",
    "api.github.com",
    "github.global.ssl.fastly.net",
    "assets-cdn.github.com",
    "raw.githubusercontent.com"
]

# 增加多个备用 DoH 接口，形成“自愈链路”
DOH_ENDPOINTS = [
    {"url": "https://dns.alidns.com/resolve", "params": {"name": "{domain}", "type": "A"}},
    {"url": "https://cloudflare-dns.com/dns-query", "headers": {"accept": "application/dns-json"}, "params": {"name": "{domain}", "type": "A"}},
    {"url": "https://doh.pub/dns-query", "params": {"name": "{domain}", "type": "A"}},
    {"url": "https://dns.google/resolve", "params": {"name": "{domain}", "type": "1"}}
]

# --- 2. 环境感知算子：检查管理员权限 ---
def check_admin_privileges():
    """
    感知当前运行环境是否具备修改 hosts 的权限。
    """
    if platform.system() == "Windows":
        try:
            is_admin = os.getuid() == 0 if hasattr(os, "getuid") else False
        except AttributeError:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        return is_admin
    else:
        return os.geteuid() == 0

# --- 3. 网络探头算子：自检并选择最稳定的 DoH 接口 ---
def probe_and_resolve(domain):
    """
    智能解析：按顺序尝试可用 DoH，自动跳过失败的链路。
    """
    for doh in DOH_ENDPOINTS:
        try:
            url = doh["url"]
            if "headers" in doh:
                headers = doh["headers"]
            else:
                headers = {}
            
            params = {}
            for key, value in doh["params"].items():
                params[key] = value.replace("{domain}", domain)
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "Answer" in data and len(data["Answer"]) > 0:
                    for answer in data["Answer"]:
                        # 优先返回第一个 A 记录（IPv4）
                        if answer.get("type") in (1, "A"):
                            print(f"    [Probe Success] Using {url} -> {answer['data']}")
                            return answer["data"]
        except Exception:
            continue
    
    print(f"    [Probe Failed] All DoH links are blocked for {domain}.")
    return None

# --- 4. 核心执行算子 ---
def get_hosts_path():
    """返回 hosts 文件路径"""
    if platform.system() == "Windows":
        return r"C:\Windows\System32\drivers\etc\hosts"
    else:
        return "/etc/hosts"

def update_hosts(new_entries):
    """安全地更新 hosts 文件，保留原有内容"""
    hosts_path = get_hosts_path()
    marker_start = "# GitHub Auto-Track Start"
    marker_end = "# GitHub Auto-Track End"
    
    try:
        with open(hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = ""
    
    # 移除旧块
    pattern = re.escape(marker_start) + r".*?" + re.escape(marker_end)
    new_content = re.sub(pattern, "", content, flags=re.DOTALL)
    
    # 构建新块
    new_block = f"\n{marker_start}\n"
    for domain, ip in new_entries.items():
        if ip:
            new_block += f"{ip} {domain}\n"
    new_block += f"{marker_end}\n"
    
    final_content = new_content.strip() + "\n" + new_block
    
    try:
        with open(hosts_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"[Success] Hosts updated: {hosts_path}")
        flush_dns()
        return True
    except PermissionError:
        print("\n[Action Required] 权限不足，请按以下步骤操作：")
        if platform.system() == "Windows":
            print("1. 右键点击‘命令提示符’或‘终端’，选择‘以管理员身份运行’")
        else:
            print("1. 在命令前加上 sudo 提升权限，例如：sudo python tianci_GH.py")
        print(f"2. 然后重新执行本脚本")

        return False

def flush_dns():
    """刷新本地 DNS 缓存"""
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["ipconfig", "/flushdns"], check=True, stdout=subprocess.DEVNULL)
        elif system == "Darwin":
            subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True)
        elif system == "Linux":
            subprocess.run(["sudo", "systemd-resolve", "--flush-caches"], check=True)
        print("[Success] DNS cache flushed.")
    except Exception:
        print("[Warning] 无法自动刷新 DNS，建议重启电脑以生效。")

# --- 5. 主程序 ---
def main():
    print("🚀 天赐范式 · GitHub DNS 加速器启动")
    
    # 权限自检
    if not check_admin_privileges():
        print("\n⚠️  提示：更新 hosts 文件需要管理员权限。")

    updated_entries = {}
    for domain in GITHUB_DOMAINS:
        print(f"🌍 正在解析 {domain} ...")
        ip = probe_and_resolve(domain)
        if ip:
            updated_entries[domain] = ip
        else:
            print(f"  ❌ 解析失败，将在脚本结束后提供手动方案。")
    
    if updated_entries:
        if update_hosts(updated_entries):
            print("\n✅ 天赐范式加速器已生效。")
    else:
        print("\n❌ 自动解析完全失败。请尝试以下手动排障步骤：")
        print("1. 检查是否能正常访问 https://dns.alidns.com")
        print("2. 尝试开启/关闭代理或 VPN")
        print("3. 若你是高级用户，可以使用 nslookup 手动查询并填入")

if __name__ == "__main__":
    main()