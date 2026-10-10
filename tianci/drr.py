# -*- coding: utf-8 -*-
"""
tianci.drr —— DRR-R：深度逆向重定向-接收型（断裂段处理，可执行化）。

来源（如实标注）：
  - 《TDP-CP与DRR-R方法论边界规范_v1.0.md》（第94天，端午整理）；核心引用：
    二、DRR-R 定义与定义域值域；2.3 三层逆向+R结构；2.4 R算子的激活条件；
    2.5 算子交换关系；2.6 典型应用场景（物理常数/理论选择两类断裂处理）。
  - 《天赐范式第93天续_1_137追问枢纽_九个断裂点的DRR收敛与R算子协同激活.md》：
    九个断裂点的 DAG、R_i 激活标志（R_i=1 需要外部输入 / R_i=0 可内部推导）、
    四直接锚定 + 五间接断裂、收敛为两个极小锚点（3维空间、作用量量子化）。

核心命题（94天 §2.1）：DRR-R 是断裂段的处理工具——TDP-CP 移交点即 DRR-R
定义域。任务是在推导无法继续时，激活 R 算子接收外部输入，追踪断裂的根因
层级，最终输出重定向结论和可证伪预言。

六层结构（94天 §2.3，顺序固定不可交换）：
  L1 直接原因    Θ_DRR溯源  —— 定位表面触发因素
  L2 结构原因    Γ_DRR拓扑  —— 定位系统性的结构缺陷
  L3 存在性原因  Σ_DRR根因  —— 定位根结构的前提条件
  R  激活        R(Ψ_A)     —— L3 无法从内部推导时接收外部输入：
                                 α(x) ↦ α(x)·f(Ψ_A(x))
  Ω_DRR 重定向              —— 从断裂点出发指向新方向
  τ_DRR 熔断                —— 输出可证伪的下一步并终止当前路径

边界裁定（94天 §2.1 + 任务单 C4 固化）：
  v7.0 基础流写作 Θ→Γ→[R?]→Σ→Φ→τ（《天赐范式算子与公式大全_v7.0》§1.2）。
  本包的裁定：`[R?]` 定标为 `[R: DRR-only]`——R 属于 DRR-R（断裂段），
  不属于 TDP-CP（白箱段）；白箱段（Φ_total ≥ 0.7）R 明确不激活。

  R 激活判据（94天 §2.4）由"是否存在形式化推导路径"决定，不由难度、
  重要性或直觉决定：
    R_i = 1  if Θ_DRR(i) = "外部输入不可回避"（无内部推导路径）
    R_i = 0  if Θ_DRR(i) = "可从系统内部推导"
  边界条件（94天 §2.2）：R 找不到外部输入源 → 标记"终极断裂"，
  输出不可证伪的终止声明——不硬凑可证伪预言（诚实约束）。

接口约定（任务单 C4 固化）：
  drr_r(handoff) -> dict
  handoff 为 TDP-CP 移交包（或同结构 dict），必须携带非空 falsifiable
  列表（可证伪预言的候选锚点）；缺失或为空一律 raise ValueError，
  不许静默降级、不许自己编造可证伪预言。

执行顺序与交换关系（94天 §2.5，代码顺序即校验顺序）：
  [L1, L2] = 0        直接原因和结构原因可逆推
  [L2, L3] ≠ 0        结构原因和存在性原因不可逆（存在性更深层）
  [L3, R] ≠ 0         存在性原因必须在 R 激活之前（先追到根，再判断）
  [R, Ω_DRR] = 0      R 激活和方向选择可交换（但方向选择依赖 R 的结果）
  [Ω_DRR, τ_DRR] ≠ 0  方向选择必须在熔断之前（先定方向，再终止当前路径）
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

from typing import Any, Dict, List

# ── 六层名称（顺序固定：L1→L2→L3→R→Ω_DRR→τ_DRR，94天 §2.3）──
DRR_LAYERS = [
    "L1 Θ_DRR溯源",     # 直接原因
    "L2 Γ_DRR拓扑",     # 结构原因
    "L3 Σ_DRR根因",     # 存在性原因
    "R激活",            # R(Ψ_A) 接收外部输入
    "Ω_DRR重定向",      # 方向选择
    "τ_DRR熔断",        # 可证伪预言
]

# ── R 算子激活标志（94天 §2.4）──
R_ON = 1   # Θ_DRR(i) = "外部输入不可回避" → 需要外部输入
R_OFF = 0  # Θ_DRR(i) = "可从系统内部推导" → 不需要外部输入

# ── 终极断裂标记（94天 §2.2 边界条件）──
ULTIMATE_BREAK = "终极断裂"

# ── 算子交换关系（94天 §2.5，文档记录；执行时代码顺序即校验顺序）──
COMMUTATORS = {
    "[L1,L2]": 0,
    "[L2,L3]": "≠0",
    "[L3,R]": "≠0",
    "[R,Ω_DRR]": 0,
    "[Ω_DRR,τ_DRR]": "≠0",
}


def _extract_break_points(handoff: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从移交包提取断裂点：优先 break_points，其次 phi_detail 中 Φ_i<1.0 的步，
    都没有则把 handoff 整体作为单断裂点处理。"""
    bp = handoff.get("break_points")
    if bp:
        return [dict(p) for p in bp]
    detail = handoff.get("phi_detail")
    if isinstance(detail, list):
        pts = [
            {"step": d.get("step", "（未命名步）"), "phi": d.get("phi"),
             "hard": (d.get("phi") is not None and float(d["phi"]) <= 0.0),
             "reason": d.get("reason", "该步路径不透明")}
            for d in detail
            if d.get("phi") is not None and float(d["phi"]) < 1.0
        ]
        if pts:
            return pts
    return [{
        "step": handoff.get("name", "（未命名断裂点）"),
        "phi": None,
        "hard": False,
        "reason": "移交包未给出断裂点坐标，按整体单断裂点处理",
    }]


def _step_category(step: str) -> str:
    """按步骤名前缀归入结构缺陷类别（供 L2 拓扑归类）。"""
    for prefix, cat in (("Θ", "溯源侧"), ("Γ", "度量侧"), ("Σ", "根因侧"),
                        ("τ", "回滚侧"), ("Φ", "门控侧"), ("Λ", "预警侧")):
        if step.startswith(prefix):
            return cat
    return "未归类"


def drr_r(handoff: Dict[str, Any]) -> Dict[str, Any]:
    """DRR-R 断裂段重定向（可执行化）。

    参数:
        handoff: dict，通常为 tdp_cp(path) 的移交包（verdict="移交"），
            必须携带非空 ``falsifiable`` 列表（可证伪预言候选锚点）。
            断裂点可附 ``r_source``（外部输入源描述，等价于 R(Ψ_A) 的 Ψ_A）；
            断裂点可附 ``derivable``（bool，内部可推导？缺省由 phi 档判定）。

    返回:
        {
          "name": 路径名,
          "phi_total": float|None,
          "layers": [六层每层的结论摘要],
          "r_activation": [{"step", "r", "source"|"reason"}, ...],
          "ultimate_break": bool（R 找不到外部输入源时为 True）,
          "termination": 终极断裂时的不可证伪终止声明（否则 None）,
          "redirect": Ω_DRR 重定向结论,
          "falsifiable": τ_DRR 输出的可证伪预言列表,
          "verdict": "白箱段需注入"|"断裂段重定向"|"终极断裂",
        }

    判定规则（任务单 C4）：
      - falsifiable 缺失或为空 → raise ValueError（不静默降级）；
      - R 的激活判据是"是否存在形式化推导路径"（94天 §2.4），
        不是难度/重要性/直觉；
      - 白箱段（Φ_total≥0.7 或 verdict="白箱"）R 明确不激活
        （[R: DRR-only]：R 属于 DRR-R，不属于 TDP-CP）。
    """
    if not isinstance(handoff, dict):
        raise ValueError("handoff 必须是 TDP-CP 移交包（dict）")

    falsifiable = handoff.get("falsifiable")
    if not isinstance(falsifiable, (list, tuple)) or len(falsifiable) == 0:
        raise ValueError(
            "DRR-R 必须携带非空 falsifiable 列表（可证伪预言候选锚点）；"
            "缺失或为空时拒绝执行，不静默降级、不编造预言")

    name = handoff.get("name", "（未命名路径）")
    phi_total = handoff.get("phi_total")
    phi_total = float(phi_total) if phi_total is not None else None
    verdict_in = handoff.get("verdict")
    is_white = (verdict_in == "白箱") or (
        phi_total is not None and phi_total >= 0.7)

    # ── L1 直接原因（Θ_DRR溯源）：定位表面触发因素 ──
    points = _extract_break_points(handoff)
    l1 = [f"{p['step']}：{p.get('reason') or '表面触发因素未注明'}"
          for p in points]

    # ── L2 结构原因（Γ_DRR拓扑）：按步骤类别归并系统性结构缺陷 ──
    seen_cats: List[str] = []
    for p in points:
        cat = _step_category(p["step"])
        if cat not in seen_cats:
            seen_cats.append(cat)
    l2 = (f"结构缺陷归并为 {len(seen_cats)} 类：{'、'.join(seen_cats) if seen_cats else '无'}"
          if not is_white else "白箱段：无结构缺陷（全路径透明）")

    # ── L3 存在性原因（Σ_DRR根因）+ R 激活（94天 §2.4）──
    # 判据：是否存在形式化推导路径。derivable=True → 内部可推导 → R_OFF；
    # derivable=False/未知 且 phi<1.0 → 外部输入不可回避 → R_ON。
    r_activation: List[Dict[str, Any]] = []
    ultimate = False
    for p in points:
        step = p["step"]
        if is_white:
            # [R: DRR-only]：白箱段 R 明确不激活（94天 §2.1 边界裁定）
            r_activation.append({
                "step": step, "r": R_OFF,
                "reason": "白箱段 R 不激活：[R: DRR-only]，R 属于 DRR-R 断裂段",
            })
            continue
        derivable = p.get("derivable")
        if derivable is None:
            phi = p.get("phi")
            derivable = not (phi is None or float(phi) < 1.0)
        if derivable:
            r_activation.append({
                "step": step, "r": R_OFF,
                "reason": "可从系统内部推导（存在形式化推导路径）",
            })
            continue
        source = p.get("r_source") or handoff.get("r_external")
        if source:
            r_activation.append({
                "step": step, "r": R_ON, "source": str(source),
                "reason": "外部输入不可回避（无内部推导路径）→ R激活接收外部输入",
            })
        else:
            # 边界条件（94天 §2.2）：R 找不到外部输入源 → 终极断裂
            ultimate = True
            r_activation.append({
                "step": step, "r": R_ON, "source": None,
                "reason": "外部输入不可回避但找不到外部输入源 → 终极断裂",
            })

    l3 = ("根因逐点判定完成："
          + "；".join(f"{a['step']}→R{'激活' if a['r'] else '不激活'}"
                      for a in r_activation))

    # ── Ω_DRR 重定向：从断裂点指向新方向 ──
    if is_white:
        redirect = "白箱段无需重定向（TDP-CP 已给出透明路径）"
        verdict = "白箱段需注入"
    elif ultimate:
        redirect = ("断裂点无外部输入源，无法从内部形式化继续；"
                    "终止当前路径，不再向前硬推")
        verdict = ULTIMATE_BREAK
    else:
        hint = handoff.get("suggest")
        redirect = hint or (
            f"沿 {len(r_activation)} 处 R 激活点接收外部输入（Ψ_A），"
            f"再回到 L1 重新溯源验证收敛")
        verdict = "断裂段重定向"

    # ── τ_DRR 熔断：输出可证伪预言并终止当前路径 ──
    if ultimate:
        termination = (
            f"终极断裂：{name} 的断裂点无法被内部形式化推导亦无外部输入源，"
            f"本路径输出不可证伪的终止声明（94天 §2.2），拒绝继续推导；"
            f"等待新的外部输入源后再重定向。")
        out_falsifiable: List[str] = []
    else:
        termination = None
        out_falsifiable = [str(f) for f in falsifiable]

    return {
        "name": name,
        "phi_total": phi_total,
        "layers": {
            "L1 Θ_DRR溯源": l1,
            "L2 Γ_DRR拓扑": l2,
            "L3 Σ_DRR根因": l3,
            "R激活": r_activation,
            "Ω_DRR重定向": redirect,
            "τ_DRR熔断": out_falsifiable,
        },
        "r_activation": r_activation,
        "ultimate_break": ultimate,
        "termination": termination,
        "redirect": redirect,
        "falsifiable": out_falsifiable,
        "verdict": verdict,
    }