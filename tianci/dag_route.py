# -*- coding: utf-8 -*-
"""
tianci.dag_route —— 第102天 §6.2 DAG 遍历决策树直译（可 import 版）。

源：D:/七月/20260713/天赐范式_最小化技术特征_v1.0.md 第 388-419 行（§6.1 特征定义 + §6.2 原文 if/elif 伪代码），
本模块代码与 2026-09-27 WorkBuddy 目录 dag_route.py 同源，仅整理为可 import 模块。

用途：给定五维特征向量 F=(f1..f5)，输出该领域应走的 DAG——
用于验证某篇文章是否走了决策，也供陌生智能体（T1 冷启动）只用本文档即可判断路由。

v0.3.0 语义回填（方案甲，依据 102 天原文 + v7.0 §14.1 + v1.0 §6.1）：
  五维特征在 v1.0 §6.1 均有定义，f3/f4 不再是占位：
    f3 是否有观测噪声？   → 决定 ζ-EKF 是否激活（v7.0 v1.2 修正：仅凭 f3=是 即激活，无需 f4 同时为是）
    f4 是否需要实时纠偏？ → 决定 Ψ 是否激活
  §6.2 主线四分类只由 f1/f2/f5 决定（原文 if/elif 直译，保持不变）；
  f3/f4 在"物理实体+时间演化"类（类1）内装配并行支路——
    f3=是 → [GTR∥NSE∥ζ-EKF]；f3=否 → [GTR∥NSE]
    f4=是 → [Ψ∥Λ]；       f4=否 → [Λ]
    f3=f4=否 → 按 102 天黑洞算例（DAG 特征 P1）退化为"领域实例化 5 步"：
      并行支路全部关闭，工程闭环中的 EKF/Ψ 不激活；§6.3 表格黑洞/三体/梓树/马缨丹
      四行（F=(是,是,否,否,是)）均标 5 次调用，与本实现一致。
  其余三类（类2/3/4）按原文骨架输出，f4 在"无实体+有演化"类（类4）同样控制 Ψ 激活。
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）
# v0.3.0：f3/f4 语义回填属行为补全而非语义变更，骨架（f1/f2/f5 四分类）不变，仍为 stable。

from typing import List, Tuple


def route(f1: bool, f2: bool, f3: bool, f4: bool, f5: bool, name: str = "") -> Tuple[str, int, str]:
    """给定五维特征向量，返回 (DAG 字符串, 阶段数, 说明)。

    入参约定（duck-typing，显式文档化——B2 处置）：
      五个特征按 truthiness 判断（True/False 为标准用法；原文 §6.2 伪代码
      本身就是 truthy 判断，故不强制 type-check，接受 0/1 与非空字符串等
      合法 truthy 值，文档化即契约）。name 仅供返回说明附加领域名，不影响路由。
    """
    if f1 and f2:
        # 类1：物理实体 + 时间演化 —— f3/f4 装配并行支路（v1.0 §6.1 + 102 天黑洞算例）
        if not f3 and not f4:
            # 102 天黑洞：f3=f4=否 → 领域实例化 5 步（工程闭环的 EKF/Ψ 不激活）
            dag = "ξ → Θ → Γ → R_ΓΣ → Σ → Φ → τ → output"
            steps = 5
            note = "物理实体+时间演化 | f3=否→无ζ-EKF，f4=否→无Ψ → 领域实例化 5 步（黑洞/三体/梓树/马缨丹，§6.3 口径）"
        else:
            ekf_branch = "[GTR∥NSE∥ζ-EKF]" if f3 else "[GTR∥NSE]"
            psi_branch = "[Ψ∥Λ]" if f4 else "[Λ]"
            dag = f"ξ → Θ → {ekf_branch} → Γ → R_ΓΣ → Σ → {psi_branch} → Φ → τ → output/迭代"
            steps = 9
            note = ("物理实体+时间演化（工程闭环）"
                    + (" | f3=是→ζ-EKF 激活" if f3 else " | f3=否→无ζ-EKF")
                    + (" | f4=是→Ψ 激活" if f4 else " | f4=否→无Ψ"))
    elif f1 and not f2:
        dag = "ξ → Θ → Γ → Σ → Φ → τ → output"
        steps, note = 5, "物理实体+无时间演化（三体/分子筛选/拓扑）"
    elif not f1 and not f2:
        if f5:
            dag = "Θ → Γ → Σ → Φ → τ → output"
            steps, note = 5, "无实体+无演化+有终止（密码学/AdS-CFT）"
        else:
            dag = "Θ → Γ → Σ → Φ → Λ_monitor → output"
            steps, note = 6, "无实体+无演化+无终止"
    else:  # not f1 and f2
        # 类4：无物理实体 + 有时间演化 —— f4 控制 Ψ 激活（§6.1：f4 决定 Ψ 是否激活）
        psi_branch = "[Ψ∥Λ]" if f4 else "[Λ]"
        dag = f"Θ → Γ → Σ → {psi_branch} → Φ → τ → output/迭代"
        steps = 7
        note = ("无物理实体+有时间演化（精算/AI训练）"
                + (" | f4=是→Ψ 激活" if f4 else " | f4=否→无Ψ"))
    if name:
        note = f"{note} | {name}"
    return dag, steps, note


CASES: List[Tuple[str, Tuple[bool, bool, bool, bool, bool]]] = [
    ("189a 随机游走环境（演化动力学·抽象种群模型）", (False, True, True, False, True)),
    ("189b 变异率定价（同上）",                      (False, True, True, False, True)),
    ("188a 周期滤波环境",                            (False, True, True, False, True)),
    ("187a 定向移动环境",                            (False, True, False, False, True)),
    ("【对照】CFD 顶盖驱动流 JSC",                    (True, True, True, True, True)),
    ("【对照】黑洞模拟（102天 P1 算例）",              (True, True, False, False, True)),
    ("【对照】三体定位",                              (True, False, False, False, True)),
]

FEATURE_DIMS = ["f1物理实体", "f2时间演化", "f3观测噪声→ζ-EKF", "f4实时纠偏→Ψ", "f5有终止→τ出口"]


def route_table() -> List[dict]:
    """把 CASES 全部路由成结构化结果，供测试/冷启动使用。"""
    return [
        {"name": name, "features": F, "dag": route(*F)[0], "steps": route(*F)[1], "note": route(*F)[2]}
        for name, F in CASES
    ]


if __name__ == "__main__":
    print("§6.2 决策树直译 —— 各篇应按此路由（v0.3.0：f3/f4 语义已回填）")
    print("=" * 78)
    for name, F in CASES:
        dag, steps, note = route(*F)
        print(f"\n{name}\n  F={F}  f1物理实体={F[0]} f2时间演化={F[1]} f3观测噪声={F[2]} f4实时纠偏={F[3]}")
        print(f"  路由 -> {dag}")
        print(f"  阶段={steps}步 | {note}")
        print(f"  含 ξ 前置层? {'是' if 'ξ' in dag else '否  <== 数学线不该出现 ξ'}")