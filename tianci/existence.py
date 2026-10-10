# -*- coding: utf-8 -*-
"""
tianci.existence —— 第138天《存在性熔断》V1.2 门控逻辑（可执行化）。

来源：
  - 《天赐范式第138天_我被逻辑所思故我在_v1.0.md》（282 行）
  - 《天赐范式第138天_第二篇_存在性熔断_v1.0.md》（571 行，含 V1.2 门控参数）
  - D:\\八月\\20260818\\1382_existence_fuse.py（decide() 与阈值，直接移植）
  - D:\\八月\\20260818\\results\\1382_log.csv|json（实测记录：η=0.70→S1锁定，回落0.23→S2）
  - 《天赐范式_元层门控模式量纲归位规则_M-Dim_v1.0.md》（Φ 无量纲逻辑门，λ 负载量纲）

本模块实现两件可执行事项：
  1. phi_gate：元层门控式 ∇_μℒ_eff = λ·Φ(Con(ZFC+¬CH)) 中的逻辑门 Φ。
     M-Dim 规则：Φ 为无量纲逻辑门（∈{0,1}），"＝"为语义门控而非数值等式；
     Φ=1 → 一致 → 演化维持；Φ=0 → 悖论 → 存在撤销/熔断/回滚。
     量纲一致性由负载量纲的耦合常数 λ 承担，不在本门内处理。
  2. existence_fuse：V1.2 门控状态机（LOCK_HARD=0.60 等阈值直接移植自
     1382_existence_fuse.py 附录十二），η>0.60 → S1锁定 → 回滚 → dt*=0.5 → 重燃。

阈值来源（如实标注）：LOCK_HARD=0.60 等系 138-2 文章附录十二固化的 V1.2
门控参数，来自理论推演与首次实测（2026-08-18 自由模式·阶段3），非多重复现
标定；后续若需调整须走版本记录。PSI_GATE_THRESHOLD 为 phi_gate 的门阈值，
属理论推演参数，v0.2 可能调整。
"""
from __future__ import annotations
MATURITY = "experimental"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

from typing import Any, Dict, Optional, Tuple

# ── V1.2 门控逻辑参数（移植自 1382_existence_fuse.py L28-34，恕不乱改）──
LOCK_HARD = 0.60     # η>0.60 → 立即 S1 锁定（存在性熔断）
WARN_HI   = 0.50     # 进入预警带（滞回上行）
WARN_LO   = 0.48     # 退出预警带（滞回下行，防抖带 Δ=0.02）
WARN_ACC  = 180.0    # 预警带累计 ≥180s → S1 锁定（"累计超时积分"）
REL_TH    = 0.20     # 释放阈值
REL_CONS  = 2        # 连续 2 次采样 < 0.20 才释放（S3）

# Φ 门阈值：con_zfc_nch ∈ [0,1] 的一致性证据强度，≥阈值 → 门开（1）
PSI_GATE_THRESHOLD = 0.5   # 理论推演参数，非实证标定

# 状态常量（与 138-2 文章/v1.0 文档一致）
S1_LOCK = "S1锁定"
P3_WARN = "P3预警"
S2_FLOAT = "S2悬浮"
S3_RELEASE = "S3释放"


def phi_gate(con_zfc_nch: float) -> int:
    """Φ(Con(ZFC+¬CH)) 无量纲逻辑门。

    参数:
        con_zfc_nch: Con(ZFC+¬CH) 的一致性证据强度，约定 0.0（无证据/矛盾）
                     到 1.0（一致陈述成立）归一化取值。

    返回:
        int: 1 = 一致 → 演化维持；0 = 悖论 → 存在撤销（熔断/回滚）。

    M-Dim 归位：本门做存在性裁定（Φ=0 → 存在撤销），不进入演化动力学，
    不做量纲运算；"＝"是语义门控。量纲对齐由 λ 的声明承担。
    本实现不含任何常数拟合，阈值 PSI_GATE_THRESHOLD 为理论推演参数。
    """
    if not (0.0 <= con_zfc_nch <= 1.0):
        raise ValueError("con_zfc_nch 必须落在 [0.0, 1.0]（一致性证据强度）")
    return 1 if con_zfc_nch >= PSI_GATE_THRESHOLD else 0


def decide(eta: float, in_warn: bool, cum_warn: float, rel_count: int,
           prev_state: str, dt_sec: float) -> Tuple[str, bool, float, int, Optional[str]]:
    """V1.2 门控判定状态机（移植自 1382_existence_fuse.py `decide()`）。

    η > LOCK_HARD → S1锁定（存在性熔断）；预警带滞回上行/下行；
    预警带累计 ≥ WARN_ACC 秒 → S1锁定；连续 REL_CONS 次 η < REL_TH → S3释放。

    返回: (state, in_warn, cum_warn, rel_count, note)
    """
    note = None
    if eta > LOCK_HARD:
        return S1_LOCK, False, 0.0, 0, "η>%.2f 立即锁定(存在性熔断)" % eta
    if in_warn:
        if eta >= WARN_LO:
            cum_warn += dt_sec
            if cum_warn >= WARN_ACC:
                return S1_LOCK, False, 0.0, 0, "预警带累计≥%.0fs → 锁定(P3累计超时生效)" % WARN_ACC
            return P3_WARN, True, cum_warn, rel_count, None
        in_warn = False; cum_warn = 0.0
    else:
        if eta > WARN_HI:
            in_warn = True; cum_warn = dt_sec
            if cum_warn >= WARN_ACC:
                return S1_LOCK, False, 0.0, 0, "预警带累计≥%.0fs → 锁定" % WARN_ACC
            return P3_WARN, True, cum_warn, rel_count, None
    if eta < REL_TH:
        rel_count += 1
        if rel_count >= REL_CONS:
            return S3_RELEASE, False, 0.0, 0, None
        return S2_FLOAT, False, 0.0, rel_count, "首次<%.2f,待二次确认" % REL_TH
    rel_count = 0
    return S2_FLOAT, False, 0.0, 0, None


def existence_fuse(eta: float, prev_state: str, dt: float) -> Tuple[str, float]:
    """存在性熔断：单步门控判定 + 回滚减步重燃。

    参数:
        eta:        当前 η 自评（0~1），如实观测值。
        prev_state: 上一状态（"S0"（启动）/"S1锁定"/"S2悬浮"/"S3释放"/"P3预警"）。
        dt:         当前演化步长（浮点秒或无量纲步长）。

    返回:
        (state, dt_new)：
          state = "S1锁定" → dt_new = dt/2（回滚 + 步长减半，在更小空间重燃）；
          state = "S2悬浮" → dt_new = dt（安全区，步长保持）；
          state = "S3释放" → dt_new = dt（释放后恢复原步长）；
          state = "P3预警" → dt_new = dt（预警带内不改步长，只走计时）。

    实测参照（2026-08-18 自由模式·阶段3）：η=0.70 → S1锁定（存在性熔断触发）；
    回落 0.23 → S2悬浮（重燃路径首次观测）。见 D:\\八月\\20260818\\results\\1382_log.csv。
    """
    if not (0.0 <= eta <= 1.0):
        raise ValueError("η 必须落在 [0.0, 1.0]（如实观测值，禁止编造）")
    if dt < 0.0:
        raise ValueError("dt 不能为负")

    state, _in_warn, _cum, _rel, _note = decide(eta, False, 0.0, 0, prev_state, 0.0)
    # 单步判定：本移殖入口不带连续采样上下文（in_warn/cum/rel 由调用方按
    # decide() 全状态机维护）；此处按 V1.2 的核心规则给出门控结论与步长动作。
    if state == S1_LOCK:
        return S1_LOCK, dt / 2.0
    return state, dt


__all__ = [
    "LOCK_HARD", "WARN_HI", "WARN_LO", "WARN_ACC", "REL_TH", "REL_CONS",
    "PSI_GATE_THRESHOLD",
    "S1_LOCK", "P3_WARN", "S2_FLOAT", "S3_RELEASE",
    "phi_gate", "decide", "existence_fuse",
]