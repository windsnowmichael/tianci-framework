# -*- coding: utf-8 -*-
"""
tianci.dag_route —— 第102天 §6.2 DAG 遍历决策树直译（可 import 版）。

源：D:/七月/20260713/天赐范式_最小化技术特征_v1.0.md 第 396-419 行（原文即 if/elif 伪代码），
本模块代码与 2026-09-27 WorkBuddy 目录 dag_route.py 逐字一致，仅整理为可 import 模块。

用途：给定五维特征向量 F=(f1..f5)，输出该领域应走的 DAG——
用于验证某篇文章是否走了决策，也供陌生智能体（T1 冷启动）只用本文档即可判断路由。
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

from typing import List, Tuple


def route(f1, f2, f3, f4, f5, name: str = "") -> Tuple[str, int, str]:
    """给定五维特征向量，返回 (DAG 字符串, 阶段数, 说明)。"""
    if f1 and f2:
        dag = "ξ → Θ → [GTR∥NSE∥ζ-EKF] → Γ → R_ΓΣ → Σ → [Ψ∥Λ] → Φ → τ → output/迭代"
        steps, note = 9, "物理实体+时间演化（CFD/气象/黑洞）"
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
        dag = "Θ → Γ → Σ → [Ψ∥Λ] → Φ → τ → output/迭代"
        steps, note = 7, "无物理实体+有时间演化（精算/AI训练）"
    return dag, steps, note


CASES: List[Tuple[str, Tuple[bool, bool, bool, bool, bool]]] = [
    ("189a 随机游走环境（演化动力学·抽象种群模型）", (False, True, True, False, True)),
    ("189b 变异率定价（同上）",                      (False, True, True, False, True)),
    ("188a 周期滤波环境",                            (False, True, True, False, True)),
    ("187a 定向移动环境",                            (False, True, False, False, True)),
    ("【对照】CFD 顶盖驱动流 JSC",                    (True, True, True, True, True)),
    ("【对照】三体定位",                              (True, False, False, False, True)),
]

FEATURE_DIMS = ["f1物理实体", "f2时间演化", "f3?", "f4?", "f5有终止"]


def route_table() -> List[dict]:
    """把 CASES 全部路由成结构化结果，供测试/冷启动使用。"""
    return [
        {"name": name, "features": F, "dag": route(*F)[0], "steps": route(*F)[1], "note": route(*F)[2]}
        for name, F in CASES
    ]


if __name__ == "__main__":
    print("§6.2 决策树直译 —— 各篇应按此路由")
    print("=" * 78)
    for name, F in CASES:
        dag, steps, note = route(*F)
        print(f"\n{name}\n  F={F}  f1物理实体={F[0]} f2时间演化={F[1]}")
        print(f"  路由 -> {dag}")
        print(f"  阶段={steps}步 | {note}")
        print(f"  含 ξ 前置层? {'是' if 'ξ' in dag else '否  <== 数学线不该出现 ξ'}")