# -*- coding: utf-8 -*-
"""
天赐范式 · GitHub IP 自适应加速器（无人值守版）
核心能力：CNAME自动追踪 + 已知IP兜底 + 智能输入处理 + 定期自动更新
"""
import os
import sys
import re
import json
import shutil
import platform
import subprocess
import logging
import concurrent.futures
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timedelta

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError

# ---------------------- 全局配置 ----------------------
# 日志配置（同时输出到文件和控制台）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("tianci_github_tracker.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 核心配置
CONFIG_FILE = "tianci_github_tracker.json"  # 持久化配置（IP+更新时间）
GITHUB_DOMAINS = [
    "github.com",
    "api.github.com",
    "github.global.ssl.fastly.net",
    "assets-cdn.github.com",
    "raw.githubusercontent.com"
]
# 优化后的DoH列表（国内优先，全球备用）
DOH_ENDPOINTS = [
    # 阿里DoH（国内最稳，优先）
    {"url": "https://dns.alidns.com/resolve", "params": {"name": "{domain}", "type": "A"}},
    # 腾讯DoH
    {"url": "https://doh.pub/dns-query", "params": {"name": "{domain}", "type": "A"}},
    # 114DNS DoH（国内备用）
    {"url": "https://doh.114dns.com/dns-query", "params": {"name": "{domain}", "type": "A"}},
    # 百度DoH（国内备用）
    {"url": "https://doh.baidu.com/dns-query", "params": {"name": "{domain}", "type": "A"}},
    # Cloudflare DoH（全球备用）
    {"url": "https://cloudflare-dns.com/dns-query", "headers": {"accept": "application/dns-json"}, "params": {"name": "{domain}", "type": "A"}},
    # Google DoH（最后备用）
    {"url": "https://dns.google/resolve", "params": {"name": "{domain}", "type": "1"}}
]
# GitHub常用CDN IP兜底库（来自官方文档+长期观测）
KNOWN_GITHUB_IPS = {
    "github.com": ["20.205.243.166", "20.205.243.167", "20.205.243.168"],
    "api.github.com": ["20.205.243.168", "20.205.243.169"],
    "github.global.ssl.fastly.net": ["157.240.16.50", "157.240.16.51"],
    "assets-cdn.github.com": ["185.199.110.133", "185.199.109.133", "185.199.111.133"],  # 与raw共用CDN
    "raw.githubusercontent.com": ["185.199.110.133", "185.199.109.133", "185.199.111.133"]
}
HOSTS_MARKER_START = "# GitHub Auto-Track Start (TianCi)"
HOSTS_MARKER_END = "# GitHub Auto-Track End"
IP_EXPIRE_HOURS = 24  # IP缓存过期时间（24小时自动更新）

# ---------------------- 工具函数 ----------------------
def get_hosts_path() -> str:
    """返回当前系统的hosts文件路径"""
    system = platform.system()
    if system == "Windows":
        return r"C:\Windows\System32\drivers\etc\hosts"
    elif system == "Darwin":  # macOS
        return "/etc/hosts"
    elif system == "Linux":
        return "/etc/hosts"
    else:
        raise OSError(f"不支持的系统: {system}")

def check_admin_privileges() -> bool:
    """检查是否具备管理员权限（跨平台）"""
    system = platform.system()
    try:
        if system == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        return False

def backup_hosts(hosts_path: str) -> bool:
    """备份hosts文件（防止改坏）"""
    backup_path = f"{hosts_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        if os.path.exists(hosts_path):
            shutil.copy2(hosts_path, backup_path)
            logger.info(f"hosts已备份到: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"备份hosts失败: {e}")
        return False

def flush_dns_cache() -> None:
    """刷新系统DNS缓存（跨平台）"""
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["ipconfig", "/flushdns"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif system == "Darwin":
            subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif system == "Linux":
            if os.path.exists("/usr/bin/systemd-resolve"):
                subprocess.run(["sudo", "systemd-resolve", "--flush-caches"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["sudo", "/etc/init.d/nscd", "restart"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("DNS缓存已刷新")
    except subprocess.CalledProcessError as e:
        logger.error(f"刷新DNS失败: {e}")
        print("⚠️ 无法自动刷新DNS，建议重启电脑以生效。")
    except Exception as e:
        logger.error(f"刷新DNS时出错: {e}")

def extract_ip(input_str: str) -> Optional[str]:
    """从字符串中提取有效IPv4/IPv6地址（自动处理格式错误）"""
    # IPv4正则（匹配x.x.x.x，每个x为1-3位数字）
    ipv4_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    # IPv6正则（匹配标准格式，简化版覆盖常见情况）
    ipv6_pattern = r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
    # 优先匹配IPv6，再匹配IPv4（避免部分匹配）
    match = re.search(ipv6_pattern, input_str) or re.search(ipv4_pattern, input_str)
    return match.group() if match else None

def verify_ip(ip: str, domain: Optional[str] = None) -> bool:
    """验证IP是否能访问GitHub（支持域名特定检查）"""
    if not ip:
        return False
    # 检查列表（优先GitHub特定资源，再通用检查）
    check_targets = [
        f"https://{ip}/favicon.ico",  # 通用资源
        f"https://{domain}/" if domain else None,  # 域名特定首页
        "https://github.com/"  # 备用GitHub主页
    ]
    for target in check_targets:
        if not target:
            continue
        try:
            response = requests.get(target, timeout=5, verify=False)  # 忽略SSL证书错误（IP访问可能不匹配域名）
            if response.status_code == 200:
                logger.info(f"✅ IP {ip} 验证通过（访问 {target} 成功）")
                return True
        except Exception as e:
            logger.debug(f"IP {ip} 验证失败（{target}）: {e}")
    # 最后尝试ping（需要权限，可能失败）
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["ping", "-n", "1", "-w", "1000", ip], capture_output=True, text=True)
        else:
            result = subprocess.run(["ping", "-c", "1", "-W", "1", ip], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ IP {ip} ping通")
            return True
    except:
        pass
    logger.warning(f"❌ IP {ip} 所有验证失败")
    return False

def probe_doh_with_cname(domain: str) -> Optional[Tuple[str, str]]:
    """
    智能解析域名：先查CNAME（别名），再查A/AAAA记录（支持多DoH并行）
    :return: (IPv4, IPv6) 或 None（解析失败）
    """
    # 第一步：查询CNAME记录（DoH type=5）
    cname_target = None
    for doh in DOH_ENDPOINTS:
        try:
            url = doh["url"]
            headers = doh.get("headers", {})
            params = {k: v.replace("{domain}", domain) for k, v in doh["params"].items()}
            params["type"] = "5"  # CNAME类型标识
            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                answers = data.get("Answer", [])
                for ans in answers:
                    if ans.get("type") == 5:  # CNAME类型
                        cname_target = ans.get("data").rstrip(".")  # 去除末尾的点（DNS格式）
                        logger.info(f"🔍 CNAME解析: {domain} -> {cname_target}")
                        break
                if cname_target:
                    break  # 找到CNAME，停止查询
        except Exception as e:
            logger.debug(f"CNAME查询失败 {doh['url']}: {e}")
            continue
    
    # 第二步：解析CNAME目标或原域名的A/AAAA记录
    target = cname_target if cname_target else domain
    logger.info(f"🎯 最终解析目标: {target}")
    
    # 多线程并行查询A（IPv4）和AAAA（IPv6）记录
    ipv4, ipv6 = None, None
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(DOH_ENDPOINTS)) as executor:
        # 提交A记录查询任务
        future_a = executor.submit(_probe_doh_record, target, "A", DOH_ENDPOINTS)
        # 提交AAAA记录查询任务
        future_aaaa = executor.submit(_probe_doh_record, target, "AAAA", DOH_ENDPOINTS)
        # 等待结果
        ipv4 = future_a.result()
        ipv6 = future_aaaa.result()
    
    return (ipv4, ipv6) if (ipv4 or ipv6) else None

def _probe_doh_record(domain: str, record_type: str, doh_list: List[Dict]) -> Optional[str]:
    """DoH单记录类型查询（内部函数，支持多DoH重试）"""
    for doh in doh_list:
        try:
            url = doh["url"]
            headers = doh.get("headers", {})
            params = {k: v.replace("{domain}", domain) for k, v in doh["params"].items()}
            params["type"] = record_type  # A或AAAA
            response = requests.get(url, headers=headers, params=params, timeout=5)
            response.raise_for_status()  # 抛出HTTP错误
            
            data = response.json()
            answers = data.get("Answer", [])
            for ans in answers:
                if ans.get("type") == record_type:
                    return ans.get("data")
        except Exception as e:
            logger.debug(f"DoH {url} 查询 {record_type} 失败: {e}")
            continue
    return None

def get_known_ip(domain: str) -> Optional[str]:
    """从已知IP库中获取域名的有效IP（兜底用）"""
    # 优先匹配 exact domain
    if domain in KNOWN_GITHUB_IPS:
        for ip in KNOWN_GITHUB_IPS[domain]:
            if verify_ip(ip, domain):
                return ip
    # 其次匹配子域名（比如assets-cdn.github.com -> github.com的IP）
    for base_domain, ips in KNOWN_GITHUB_IPS.items():
        if base_domain in domain:
            for ip in ips:
                if verify_ip(ip, domain):
                    return ip
    return None

# ---------------------- 核心业务逻辑 ----------------------
def update_hosts_file(entries: Dict[str, Tuple[str, str]]) -> bool:
    """
    安全更新hosts文件（保留原有内容，仅替换标记块）
    :param entries: 域名到(IPv4, IPv6)的映射
    :return: 是否成功
    """
    hosts_path = get_hosts_path()
    if not os.path.exists(hosts_path):
        logger.error(f"hosts文件不存在: {hosts_path}")
        return False
    
    # 1. 备份hosts（防止改坏）
    if not backup_hosts(hosts_path):
        if not confirm("⚠️ hosts备份失败，是否继续更新？(y/n): "):
            return False
    
    # 2. 读取原hosts内容
    try:
        with open(hosts_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"读取hosts失败: {e}")
        return False
    
    # 3. 移除旧的标记块
    pattern = re.compile(re.escape(HOSTS_MARKER_START) + r".*?" + re.escape(HOSTS_MARKER_END), re.DOTALL)
    new_content = pattern.sub("", content)
    
    # 4. 构建新的标记块（仅保留有效IP）
    new_block = [f"\n{HOSTS_MARKER_START}\n"]
    for domain, (ipv4, ipv6) in entries.items():
        if ipv4:
            new_block.append(f"{ipv4} {domain}\n")
        if ipv6:
            new_block.append(f"{ipv6} {domain}\n")
    new_block.append(f"{HOSTS_MARKER_END}\n")
    
    # 5. 写入新内容
    final_content = new_content.strip() + "\n" + "\n".join(new_block)
    try:
        with open(hosts_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        logger.info(f"✅ hosts文件已更新: {hosts_path}")
        flush_dns_cache()  # 刷新DNS
        return True
    except PermissionError:
        logger.error("❌ 权限不足，无法写入hosts")
        print_permission_tips()
        return False
    except Exception as e:
        logger.error(f"❌ 写入hosts失败: {e}")
        # 恢复备份
        if os.path.exists(f"{hosts_path}.bak"):
            shutil.copy2(f"{hosts_path}.bak", hosts_path)
            logger.info("✅ 已恢复hosts备份")
        return False

def print_permission_tips() -> None:
    """打印权限提升提示"""
    system = platform.system()
    print("\n" + "=" * 60)
    print("❌ 需要管理员权限才能修改hosts文件！")
    if system == "Windows":
        print("1. 右键点击本脚本/终端，选择「以管理员身份运行」")
    else:
        print("1. 在命令前加sudo，例如: sudo python tianci_github_tracker.py")
    print("2. 重新运行脚本")
    print("=" * 60)

def confirm(prompt: str) -> bool:
    """简单的用户确认函数"""
    while True:
        resp = input(prompt).strip().lower()
        if resp in ("y", "yes"):
            return True
        elif resp in ("n", "no"):
            return False
        print("请输入 y 或 n。")

def load_config() -> Dict:
    """加载持久化配置（IP+更新时间）"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {}
    return {}

def save_config(config: Dict) -> None:
    """保存持久化配置"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"配置已保存到: {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"保存配置失败: {e}")

# ---------------------- 主程序 ----------------------
def main():
    logger.info("🚀 天赐范式 · GitHub IP 自适应加速器（无人值守版）启动")
    
    # 1. 权限检查
    if not check_admin_privileges():
        logger.error("❌ 权限不足")
        print_permission_tips()
        return
    
    # 2. 加载配置
    config = load_config()
    current_time = datetime.now()
    updated_entries = {}  # 最终要写入hosts的条目
    domains_to_resolve = []  # 需要重新解析的域名
    
    # 3. 优先使用配置中的有效IP（未过期+验证通过）
    for domain in GITHUB_DOMAINS:
        if domain in config:
            last_ipv4, last_ipv6, last_update = config[domain]
            # 检查是否过期
            if (current_time - datetime.fromisoformat(last_update)).total_seconds() < IP_EXPIRE_HOURS * 3600:
                # 验证IP是否有效
                if (last_ipv4 and verify_ip(last_ipv4, domain)) or (last_ipv6 and verify_ip(last_ipv6, domain)):
                    logger.info(f"✅ 使用缓存IP（未过期）: {domain} -> IPv4={last_ipv4}, IPv6={last_ipv6}")
                    updated_entries[domain] = (last_ipv4, last_ipv6)
                else:
                    logger.info(f"⚠️ 缓存IP失效，重新解析: {domain}")
                    domains_to_resolve.append(domain)
            else:
                logger.info(f"⚠️ 缓存IP过期（超过{IP_EXPIRE_HOURS}小时），重新解析: {domain}")
                domains_to_resolve.append(domain)
        else:
            domains_to_resolve.append(domain)
    
    # 4. 解析需要更新的域名（多线程+CNAME+已知IP兜底）
    if domains_to_resolve:
        logger.info(f"🔍 需要解析的域名: {domains_to_resolve}")
        for domain in domains_to_resolve:
            logger.info(f"\n===== 开始解析 {domain} =====")
            # 第一步：DoH解析（CNAME+A/AAAA）
            ipv4, ipv6 = probe_doh_with_cname(domain)
            # 第二步：已知IP兜底
            if not ipv4 and not ipv6:
                logger.warning(f"⚠️ DoH解析 {domain} 失败，尝试已知IP库")
                known_ip = get_known_ip(domain)
                if known_ip and verify_ip(known_ip, domain):
                    ipv4 = known_ip  # 已知IP库只有IPv4
                    logger.info(f"✅ 已知IP兜底成功: {domain} -> {ipv4}")
            # 第三步：手动输入（最后手段，自动提取IP）
            if not ipv4 and not ipv6:
                logger.error(f"❌ 所有自动解析失败: {domain}")
                while True:
                    user_input = input(f"\n⚠️ 请手动输入 {domain} 的有效IP（IPv4/IPv6，或回车跳过）: ").strip()
                    if not user_input:
                        logger.warning(f"# {domain} 的解析")
                        break
                    # 自动提取IP
                    extracted_ip = extract_ip(user_input)
                    if extracted_ip and verify_ip(extracted_ip, domain):
                        ipv4 = extracted_ip
                        logger.info(f"✅ 手动IP验证通过: {domain} -> {ipv4}")
                        break
                    else:
                        print("❌ 无效IP或无法访问GitHub，请重新输入（格式：IPv4如1.2.3.4，IPv6如2001:db8::1）")
            # 保存结果
            if ipv4 or ipv6:
                updated_entries[domain] = (ipv4, ipv6)
                config[domain] = (ipv4, ipv6, current_time.isoformat())  # 更新配置
    
    # 5. 保存配置
    save_config(config)
    
    # 6. 更新hosts文件
    if updated_entries:
        if update_hosts_file(updated_entries):
            logger.info("=" * 60)
            logger.info("✅ 天赐范式GitHub加速器已生效！")
            logger.info("现在可以尝试访问 GitHub，速度应该更快了～")
            logger.info("IP会每24小时自动更新，无需手动操作！")
            logger.info("=" * 60)
        else:
            logger.error("❌ 更新hosts失败")
    else:
        logger.error("❌ 无有效IP可更新，请检查网络或手动输入")

if __name__ == "__main__":
    main()
