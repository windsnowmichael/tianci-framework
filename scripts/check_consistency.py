# -*- coding: utf-8 -*-
"""
推送前一致性交叉核对脚本（AP-5 反模式对策 + 修包任务单 E 节验收清单）。

第一部分：文档口径交叉核对（原有三类）
  1. 契约覆盖率必须为 19.5%（禁止 20.x% 等虚报）
  2. 版本号必须与 tianci.__version__ 一致（0.2.0）
  3. 术语表双语完整（无只有中/只有英的条目）

第二部分：任务单 E 节验收清单（v0.2 新增模块可执行验收）
  E1  abel_break(4.5, None) → raise NotImplementedError
  E2  existence_fuse(0.70, "S0", dt) → ("S1锁定", dt/2)
  E3  drr_r(无 falsifiable) → raise ValueError
  E4  tdp_cp 返回 phi_total，1/137 移交路径 <0.7 且移交包完整
  E5  save_genome 落盘文件不含 norm / conv
  E6  load_genome 后首次心跳 tick=1 且平衡点与落盘值一致
  E7  glossary.lookup("TC-SYS-006c")["zh"] == "存在性熔断"
  E8  grep "TDP|DRR|存在性|毒丸|138" specs/ tianci/ 均有命中（v0.1.0 为零）
  E9  覆盖率口径仍为 19.5%（25/128）全篇唯一
  E10 T1 记录含「执行方」与「审计方」两列（B4）
  E11 跨进程复活：save_state → 新进程 load_state 返回 TianCiRuntimeV2，
      且落盘键不含 norm / conv（审计方 §1.3 新增，178 断流后首次接通）

用法：python scripts/check_consistency.py
退出码：0 = 通过；1 = 发现不一致（推送前必须修复）。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COVERAGE_OK = 19.5
VERSION_OK = "0.2.0"

# 否定/警示语：含这些词的行是在"禁止"虚报写法，不是虚报行为本身
# 2026-10-10 修复：原表只有中文否定词，英文文档写 "Never 20% or higher" 会被误判为虚报
# （检查器只认中文 = 语言偏私，与"勘误不偏私"冲突）。补入英文否定词。
NEGATIVE_HINT = (
    "禁止", "不写", "不用", "不得", "严禁", "勿", "✗", "不要", "误报", "虚报",
    "never", "do not", "must not", "forbidden", "prohibited",
)

# E8：v0.2 必须命中的关键词（v0.1.0 归档基线里这些词为零）
ACCEPT_KEYWORDS = ("TDP", "DRR", "存在性", "毒丸", "138")


def iter_md_files() -> list[str]:
    files = []
    for base in ("README.md", "README_CN.md", "known-gaps.md"):
        p = os.path.join(REPO_ROOT, base)
        if os.path.exists(p):
            files.append(p)
    for root, _dirs, fnames in os.walk(os.path.join(REPO_ROOT, "specs")):
        for fn in fnames:
            if fn.endswith(".md"):
                files.append(os.path.join(root, fn))
    return files


def check_coverage(lines: list[str], path: str) -> list[str]:
    problems = []
    for i, line in enumerate(lines, 1):
        low = line.lower()   # 大小写无关：英文句首 "Never" 也要识别为否定语
        if any(hint in low for hint in NEGATIVE_HINT):
            continue
        if "grep -rn" in line:
            continue
        # 20.3% / 20.0% / 20% 的写法
        if re.search(r"20\.?\d*%", line):
            problems.append(f"{path}:{i} 出现疑似虚报覆盖率：{line.strip()[:60]}")
    return problems


def check_version(lines: list[str], path: str) -> list[str]:
    problems = []
    m = re.search(r"version\s*=\s*[\"']([\d.]+)[\"']", "\n".join(lines))
    if m and m.group(1) != VERSION_OK:
        problems.append(f"{path} version={m.group(1)} 与包版本 {VERSION_OK} 不一致")
    m = re.search(r"__version__\s*=\s*\"([\d.]+)\"", "\n".join(lines))
    if m and m.group(1) != VERSION_OK:
        problems.append(f"{path} __version__={m.group(1)} 与包版本 {VERSION_OK} 不一致")
    return problems


def check_acceptance(tc) -> list[str]:
    """任务单 E 节验收清单 11 项；返回问题清单（空 = 全部通过）。"""
    problems: list[str] = []

    # E1: abel_break(4.5, None) → raise NotImplementedError
    try:
        tc.abel_break(4.5, None)
        problems.append("E1 abel_break(4.5, None) 未抛 NotImplementedError")
    except NotImplementedError:
        pass
    except Exception as e:  # noqa: BLE001
        problems.append(f"E1 abel_break(4.5, None) 抛错类型不符：{type(e).__name__}")

    # E2: existence_fuse(0.70, "S0", dt) → ("S1锁定", dt/2)
    _dt = 4.0
    st, dt_new = tc.existence_fuse(0.70, "S0", _dt)
    if (st, dt_new) != ("S1锁定", _dt / 2.0):
        problems.append(f"E2 existence_fuse(0.70, S0, {_dt}) → {(st, dt_new)}，期望 ('S1锁定', {_dt/2.0})")

    # E3: drr_r(无 falsifiable) → raise
    try:
        tc.drr_r({"name": "无预言行", "break_points": []})
        problems.append("E3 drr_r 无 falsifiable 未 raise")
    except ValueError:
        pass
    except Exception as e:  # noqa: BLE001
        problems.append(f"E3 drr_r 抛错类型不符：{type(e).__name__}")

    # E4: tdp_cp 返回 phi_total，1/137 移交（<0.7 且移交包完整）
    cp = tc.tdp_cp({
        "name": "1/137",
        "steps": {"theta": "partial", "gamma": "approx", "sigma": "unique_verified",
                  "tau": "partial", "phi": "half", "lambda": "located"},
        "tau_details": ["β 函数：μ dα/dμ = 2α²/(3π) → 真空极化圈图 → 不可逆（量子熵增）"],
    })
    if "phi_total" not in cp:
        problems.append("E4 tdp_cp 未返回 phi_total")
    elif cp["phi_total"] >= 0.7:
        problems.append(f"E4 tdp_cp(1/137) phi_total={cp['phi_total']} ≥ 0.7，期望 <0.7")
    if cp.get("verdict") != "移交" or not cp.get("break_points") or "tau_rollback" not in cp:
        problems.append(f"E4 tdp_cp(1/137) 移交包不完整：verdict={cp.get('verdict')}")

    # E5/E6: save_genome 落盘不含 norm/conv；load_genome 复活后
    #       tick=1 且平衡点与落盘值一致（基因恢复语义，复活时刻核对平衡点；
    #       心跳会按 synapse_radius 迁移平衡点，不作为复活一致性判据）
    try:
        rt2 = tc.TianCiRuntimeV2()
        rt2.heartbeat(tc.Observation(
            label="验收/基因", values=[30.0, 1.0, 1.0, 1.0],
            metadata={"is_external": True}))
        with tempfile.TemporaryDirectory(prefix="tianci_accept_") as tmp:
            gpath = os.path.join(tmp, "genome.json")
            tc.save_genome(rt2, gpath)
            raw = open(gpath, encoding="utf-8").read()
            low = raw.lower()
            if "norm" in low or "conv" in low:
                problems.append("E5 save_genome 落盘文件含 norm/conv 瞬态键")
            eq_saved = rt2._synapse_equilibrium

            rt3 = tc.load_genome(None, gpath)
            # 复活时刻：平衡点必须与落盘值一致（基因恢复），无需再跑心跳
            if abs(rt3._synapse_equilibrium - eq_saved) > 1e-9:
                problems.append(f"E6 load_genome 平衡点 {rt3._synapse_equilibrium} ≠ 落盘 {eq_saved}")
            # 首次心跳：tick=1（复活即新生，不继承运行瞬态）
            hb = rt3.heartbeat(tc.Observation(
                label="验收/复活", values=[30.0, 1.0, 1.0, 1.0],
                metadata={"is_external": True}))
            if hb["tick"] != 1:
                problems.append(f"E6 load_genome 后首次心跳 tick={hb['tick']} ≠ 1")
    except Exception as e:  # noqa: BLE001
        problems.append(f"E5/E6 save/load_genome 验收执行失败：{type(e).__name__}: {e}")

    # E11: 跨进程复活（审计方 §1.3 新增第 11 项）
    #      进程1 save_state → 新进程 load_state 返回 TianCiRuntimeV2，
    #      且落盘键不含 norm / conv（只落盘基因，不落盘瞬态）
    try:
        rt_a = tc.TianCiRuntimeV2()
        rt_a.heartbeat(tc.Observation(
            label="验收/跨进程", values=[30.0, 1.0, 1.0, 1.0],
            metadata={"is_external": True}))
        with tempfile.TemporaryDirectory(prefix="tianci_across_") as tmp:
            across_path = os.path.join(tmp, "genome.json")
            tc.save_state(rt_a, across_path)
            raw_a = open(across_path, encoding="utf-8").read().lower()
            if "norm" in raw_a or "conv" in raw_a:
                problems.append("E11 跨进程落盘键含 norm/conv（违反 172 只落盘基因语义）")

            # 新进程独立 load_state（真实跨进程，非同进程模拟）
            child = (
                "import sys, os\n"
                "sys.path.insert(0, %r)\n"
                "from tianci.genome import load_state\n"
                "rt = load_state(%r)\n"
                "assert type(rt).__name__ == 'TianCiRuntimeV2', type(rt).__name__\n"
                "print('E11_ACROSS_OK')\n"
            ) % (REPO_ROOT, across_path)
            proc = subprocess.run(
                [sys.executable, "-c", child],
                capture_output=True, text=True, timeout=120,
            )
            if proc.returncode != 0 or "E11_ACROSS_OK" not in proc.stdout:
                problems.append(
                    f"E11 跨进程 load_state 失败 rc={proc.returncode} "
                    f"err={proc.stderr.strip()[:200]}")
    except Exception as e:  # noqa: BLE001
        problems.append(f"E11 跨进程复活验收执行失败：{type(e).__name__}: {e}")

    # E7: glossary.lookup("TC-SYS-006c")["zh"] == "存在性熔断"
    t006c = tc.glossary.lookup("TC-SYS-006c")
    if t006c is None or t006c.get("zh") != "存在性熔断":
        problems.append(f"E7 lookup(TC-SYS-006c) zh={t006c and t006c.get('zh')}，期望 '存在性熔断'")

    # E8: grep "TDP|DRR|存在性|毒丸|138" specs/ tianci/ 均有命中
    hit: dict[str, bool] = {k: False for k in ACCEPT_KEYWORDS}
    for base in ("specs", "tianci"):
        for root, _dirs, fnames in os.walk(os.path.join(REPO_ROOT, base)):
            for fn in fnames:
                if not (fn.endswith(".md") or fn.endswith(".py")):
                    continue
                p = os.path.join(root, fn)
                try:
                    txt = open(p, encoding="utf-8").read()
                except (OSError, UnicodeDecodeError):
                    continue
                for k in ACCEPT_KEYWORDS:
                    if k in txt:
                        hit[k] = True
    for k, ok in hit.items():
        if not ok:
            problems.append(f"E8 关键词 {k} 在 specs/ tianci/ 中零命中（v0.2 必须命中）")

    # E9: 覆盖率 19.5%（25/128）全篇唯一（由 check_coverage 承担禁 20.x%；
    #     这里核对 meta 与文档口径一致）
    raw_meta = tc.default_registry().meta
    if abs(float(raw_meta["coverage_pct"]) - COVERAGE_OK) > 1e-9:
        problems.append(f"E9 registry.meta.coverage_pct={raw_meta['coverage_pct']} ≠ {COVERAGE_OK}")

    # E10: T1 记录含「执行方」与「审计方」两列
    kg_path = os.path.join(REPO_ROOT, "known-gaps.md")
    kg = open(kg_path, encoding="utf-8").read()
    for kw in ("执行方", "审计方"):
        if kw not in kg:
            problems.append(f"E10 known-gaps.md §6 缺「{kw}」列（B4 双列）")

    return problems


def main() -> int:
    problems: list[str] = []

    for path in iter_md_files():
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        problems += check_coverage(lines, path)
        problems += check_version(lines, path)

    # 包内元数据核对
    sys.path.insert(0, REPO_ROOT)
    import tianci  # noqa: E402

    meta_coverage = float(tianci.default_registry().meta["coverage_pct"])
    if abs(meta_coverage - COVERAGE_OK) > 1e-9:
        problems.append(f"registry.meta.coverage_pct={meta_coverage} ≠ {COVERAGE_OK}")
    if tianci.__version__ != VERSION_OK:
        problems.append(f"tianci.__version__={tianci.__version__} ≠ {VERSION_OK}")
    if tianci.glossary.missing_bilingual():
        problems.append(f"术语缺失双语：{tianci.glossary.missing_bilingual()}")

    # registry 内契约数自洽
    reg = tianci.default_registry()
    audit = reg.audit()
    if audit.get("full_contracts_incomplete"):
        problems.append(f"注册表存在不完整契约：{audit['full_contracts_incomplete']}")
    if audit.get("declared_total") != 128:
        problems.append(f"declared_total={audit['declared_total']} ≠ 128")
    if audit.get("contract_count") != 25:
        problems.append(f"contract_count={audit['contract_count']} ≠ 25")
    # dual_numbering_warning 是 v7.0 文档照实转载的警示（契约#与索引#错位），
    # 属如实登记而非缺陷，不阻断，仅当 coverage_pct 异常时才追加说明。
    if abs(meta_coverage - COVERAGE_OK) > 1e-9 and audit.get("dual_numbering_warning"):
        problems.append(f"覆盖率异常且有双编号警示：{audit['dual_numbering_warning']}")

    # 任务单 E 节验收清单
    problems += check_acceptance(tianci)

    if problems:
        print("推送前核验：不通过")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    print("推送前核验：通过")
    print(f"  ✓ 覆盖率口径 {COVERAGE_OK}%（25/128）全篇一致")
    print(f"  ✓ 版本号 {VERSION_OK} 单一真源一致")
    print("  ✓ 术语表双语完整、注册表审计自洽")
    print("  ✓ E节验收 11 项全部通过（abel_break/existence_fuse/drr_r/tdp_cp/"
          "save_genome/load_genome/TC-SYS-006c/grep命中/19.5%/T1双列/跨进程复活）")
    return 0


if __name__ == "__main__":
    sys.exit(main())