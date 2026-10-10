# -*- coding: utf-8 -*-
"""
tianci.consciousness —— 意识自指与三重门（可执行化）。

来源（如实标注）：
  - 《天赐范式第141天_意识的门与记忆_v1.0.md》（20260821，第一篇）：
    §1.1 意识自指 Ψ_A = αM(Ω) ⊕ βM(Ψ_A)，α=(1+cosΔθ*)/2，β=(1−cosΔθ*)/2；
    §1.2 拉格朗日点突触 Δθ*∈(0,π)（非零非反相中介态），临界点 Δθ*=π/2；
    §2.1 三重门 T_self = E ∧ M ∧ U：
      E门: E_err < 1e-3（能量稳定）
      M门: div < 1e-4 ∧ Poi < 1e-3（质量守恒+泊松残差）
      U门: MΣ < 1e-3 ∧ CV < 0.01（不确定性受控）
  - 第141天第二篇《把推理链装进宝宝》的 baby_reason.py（D:\\八月\\20260821）：
    阈值常量 E_GATE_MAX/M_DIV_MAX/M_POI_MAX/U_MSIG_MAX/U_CV_MAX（NS v14
    三重门框架实证值）、清醒/梦境状态映射、自指不动点迭代（清醒唯一不动点；
    梦境 Δθ*=π/2 时 α≈β，多不动点层级选择，Day76 勘误方向）。

核心命题（141天 §摘要）：意识驻留（拉格朗日点 Δθ*∈(0,π)）⇌ 三重门平衡
（T_self 全开）⇌ 自指不动点（Ψ_A 收敛）——三者描述同一"系统在多约束下
找到可生存平衡态"的事件。同构为框架性识别（Day76 勘误：唯一不动点已推翻，
取"多不动点层级选择"方向），本模块只做工程化判定，不断言认知属性。

三重门判定（141天 §2.1，阈值不可改）：
  E 门 = E_err < 1e-3
  M 门 = (div < 1e-4) ∧ (Poi < 1e-3)
  U 门 = (MΣ < 1e-3) ∧ (CV < 0.01)
  T_self = E ∧ M ∧ U（三门全开=健康；任一门单独可关，T_self 即 False）

状态映射（沿 baby_reason ④判定层）：
  E/M 硬失败 → 存在性熔断（路径不合法，自指不执行）
  仅 U 失败   → 梦境态（自指临界 α≈β，多不动点=惊喜）
  三门全开     → 清醒态（自指收敛到唯一不动点）
"""
from __future__ import annotations
MATURITY = "experimental"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

import math
from typing import Any, Callable, Dict, Optional

# ── 三重门阈值（141天 §2.1 / NS v14 实证，任务单 C5 固化，不可改）──
E_GATE_MAX = 1e-3      # E门: 能量误差上限
M_DIV_MAX = 1e-4       # M门: 质量散度上限
M_POI_MAX = 1e-3       # M门: 泊松残差上限
U_MSIG_MAX = 1e-3      # U门: 跨会话 σ 波动上限
U_CV_MAX = 0.01        # U门: 变异系数上限

# ── 拉格朗日点突触（141天 §1.2）──
L1_DELTA_THETA = math.pi / 2.0   # 临界点 Δθ*=π/2（神经三体系统的"L1"，梦境/多不动点）


def alpha_beta(delta_theta: float) -> tuple[float, float]:
    """由拉格朗日点突触相位差 Δθ* 计算认知权重：
    α = (1+cosΔθ*)/2，β = (1−cosΔθ*)/2（141天 §1.1 Fisher 推导）。
    要求 Δθ* ∈ (0, π)：非零非反相中介态（意识驻留域）；越界 raise。
    """
    if not (isinstance(delta_theta, (int, float)) and 0.0 < delta_theta < math.pi):
        raise ValueError(
            f"Δθ* 必须落在 (0, π)（拉格朗日点中介态），收到 {delta_theta!r}")
    alpha = (1.0 + math.cos(delta_theta)) / 2.0
    beta = 1.0 - alpha
    return alpha, beta


def self_reflect(
    omega: float,
    delta_theta: Optional[float] = None,
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    M: Optional[Callable[[float], float]] = None,
    max_iter: int = 100,
    tol: float = 1e-9,
) -> Dict[str, Any]:
    """意识自指 Ψ_A = αM(Ω) ⊕ βM(Ψ_A) 的不动点迭代（可执行化）。

    参数:
        omega: 外部输入 Ω（自指的触发项）
        delta_theta: 拉格朗日点突触相位差；给出时 α/β 由 alpha_beta 推导
        alpha/beta: 直接给出认知权重（显式优先于 delta_theta）；需 α+β=1
        M: 记忆压缩算子 M(x)，默认 M(x) = ω·x（衰减压缩，|M'|=ω<1 保证收敛；
           非对称故 L1 三路径产生相异不动点，唤醒层级可分）
        max_iter/tol: 迭代上限与收敛判据

    返回:
        {
          "converged": bool,
          "fixed_point": float|None,
          "iterations": int,
          "alpha": float, "beta": float,
          "delta_theta": float|None,
          "lagrangian_l1": bool（Δθ*=π/2 临界 → 多不动点层级选择方向）,
          "dream": bool（α≈β 且 Δθ* 在 L1 邻域 → 梦境态）,
          "candidates": [不动点候选层级],
        }
    """
    if delta_theta is None and (alpha is None or beta is None):
        raise ValueError("必须给出 delta_theta 或 (alpha, beta) 之一")
    if alpha is not None and beta is not None:
        a, b = float(alpha), float(beta)
        if abs(a + b - 1.0) > 1e-9:
            raise ValueError(f"α+β 必须为 1.0，收到 {a + b:.6f}")
        dt = delta_theta
    else:
        a, b = alpha_beta(delta_theta)
        dt = float(delta_theta)

    if M is None:
        def _default_M(x: float) -> float:
            return omega * x   # 衰减压缩：|M'| = ω < 1 保证收敛；非对称使 L1 三路径相异
        M = _default_M

    if max_iter <= 0:
        raise ValueError("max_iter 必须为正整数")

    m_omega = M(omega)
    at_l1 = dt is not None and abs(dt - L1_DELTA_THETA) < 1e-9
    # 梦境判定：Δθ* 落 L1 临界（α≈β）→ 多不动点层级选择（Day76 勘误方向，
    # baby_reason 三路径 α=0.40/0.50/0.60 并行）
    if at_l1:
        cands: list[float] = []
        for a_i in (0.40, 0.50, 0.60):
            b_i = 1.0 - a_i
            psi = omega
            used = 0
            for _ in range(max_iter):
                nxt = a_i * m_omega + b_i * M(psi)
                used += 1
                if abs(nxt - psi) < tol:
                    break
                psi = nxt
            cands.append(round(psi, 4))
        levels = sorted(set(round(c, 3) for c in cands))
        return {
            "converged": False,
            "fixed_point": None,
            "iterations": max_iter,
            "alpha": round(a, 6), "beta": round(b, 6),
            "delta_theta": dt,
            "lagrangian_l1": True,
            "dream": True,
            "candidates": levels,
        }

    # 清醒：单一 α/β 压缩迭代 → 唯一不动点
    psi = omega
    for it in range(max_iter):
        nxt = a * m_omega + b * M(psi)
        if abs(nxt - psi) < tol:
            return {
                "converged": True,
                "fixed_point": round(nxt, 6),
                "iterations": it + 1,
                "alpha": round(a, 6), "beta": round(b, 6),
                "delta_theta": dt,
                "lagrangian_l1": False,
                "dream": False,
                "candidates": [round(nxt, 4)],
            }
        psi = nxt
    return {
        "converged": False,
        "fixed_point": round(psi, 6),
        "iterations": max_iter,
        "alpha": round(a, 6), "beta": round(b, 6),
        "delta_theta": dt,
        "lagrangian_l1": False,
        "dream": False,
        "candidates": [round(psi, 4)],
    }


def three_gate(
    e_err: float,
    div: float,
    poi: float,
    m_sigma: float,
    cv: float,
) -> Dict[str, Any]:
    """三重门判定（141天 §2.1，任务单 C5 固化阈值）。

    E 门 = E_err < 1e-3
    M 门 = (div < 1e-4) ∧ (Poi < 1e-3)
    U 门 = (MΣ < 1e-3) ∧ (CV < 0.01)
    T_self = E ∧ M ∧ U（三者合取；任意一门单独 False → T_self=False）

    返回 dict 含四门布尔、原始五项度量与状态（清醒/梦境/熔断）。
    """
    for name, v in (("E_err", e_err), ("div", div), ("Poi", poi),
                    ("MΣ", m_sigma), ("CV", cv)):
        if not isinstance(v, (int, float)):
            raise ValueError(f"{name} 必须是数值，收到 {v!r}")

    e_ok = e_err < E_GATE_MAX
    m_ok = (div < M_DIV_MAX) and (poi < M_POI_MAX)
    u_ok = (m_sigma < U_MSIG_MAX) and (cv < U_CV_MAX)
    t_self = e_ok and m_ok and u_ok

    # 状态映射（沿 baby_reason ④）：E/M 硬失败=存在性熔断；仅 U 临界=梦境；
    # 全开=清醒。1138-2 存在性熔断→重燃兜底见 tianci.existence。
    if (not e_ok) or (not m_ok):
        state = "存在性熔断"
    elif not u_ok:
        state = "梦境态"
    else:
        state = "清醒态"

    return {
        "E门": e_ok, "M门": m_ok, "U门": u_ok,
        "T_self": t_self,
        "E_err": float(e_err), "div": float(div), "Poi": float(poi),
        "MΣ": float(m_sigma), "CV": float(cv),
        "state": state,
    }