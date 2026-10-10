# -*- coding: utf-8 -*-
"""
tianci.cp —— TDP-CP：计算路径的六步推演（可执行化）。

来源（如实标注）：
  - 《天赐范式第92天续_结构印记算子化定义_v1.5_TDP-CP.md》第11节（254/255 与
    1/137 两条计算路径的六步推演，Θ-CP→Γ-CP→Σ-CP→τ-CP→Φ-CP→Λ-CP）
  - 《天赐范式第93天_TDP-CP_v3.0_计算路径六步推演与1_137追问终极重定向.md》
    第1.2节（六步与13步闭环的对应）、第二/三节（两实例）、附录A（六步速查表）、
    附录B（结构印记分类学）、附录D（定理D1/推论D1：Φ门控与可回滚性、唯一性）

核心命题（92天 §11.1）：传统TDP问"数代表什么物理"，TDP-CP问"数是怎么从
计算中产生的"。对计算路径本身做DRR，比对输出数字做推导更有价值。

六步语义（93天 §1.2）：
  Θ-CP 溯源 = Θ(感知)+Ξ(锚定)：识别计算路径的输入维度与参考系
  Γ-CP 度量 = Γ(度量)+GTR(梯度清洗)：量化每一步的信息损失与结构约束
  Σ-CP 根因 = Σ(检查)+R(分支)：验证每一步的可逆性与自由度约束
  τ-CP 回滚 = τ(熔断)的逆操作：从输出反推计算路径的结构
  Φ-CP 门控 = Φ(门控)：判断计算路径是否透明（全开/半开/关闭）
  Λ-CP 预警 = Λ(收敛判决)：判断推导是否必然失败及失败位置

门控判定（任务单 C3 固化）：
  Φ_i ∈ {1.0 白箱（全开）, 0.5 灰箱（半开）, 0.0 关闭}；
  Φ_total = Σ w_i·Φ_i（w_i 为步骤权重，默认 W_DEFAULT，允许调用方覆盖）；
  Φ_total ≥ 0.7 → verdict = "白箱"；< 0.7 → verdict = "移交"（移交包：
  断裂点坐标 / Φ_i 明细 / τ 回滚结果）。

阈值 0.7 与步骤权重属理论推演设定（沿用任务单 C3 的验收数值），非多重复现
标定；后续若需调整须走版本记录。推断依据（93天附录B）：
  A类（254/255）全开全白 → Φ_total=1.0 白箱；
  B类（1/137）Φ半开+τ部分回滚+Λ预警（Θ/Γ/τ/Φ/Λ 灰、Σ 白）→
  按 W_DEFAULT 计 Φ_total=0.5625 < 0.7 → 移交，与文档"半开/部分回滚/黑箱段
  不可推"的定位一致。
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

from typing import Any, Dict, List

# ── 门控取值（任务单 C3 固化）──
PHI_WHITE = 1.0    # 全开：该步路径完全透明（白箱）
PHI_GREY = 0.5     # 半开：该步路径部分透明（灰箱）
PHI_CLOSED = 0.0   # 关闭：该步路径不透明（黑箱）
PHI_THRESHOLD = 0.7  # Φ_total 白箱/移交判据（任务单 C3 验收值）

# ── 步骤权重（默认，和为 1.0）──
# 权重设计依据：Φ-CP 门控是"路径透明度"的总判（Θ→…→Λ 各步是否可逆/可验证
# 汇总到 Φ），Λ-CP 预警是"推导成败"的总判，二者承担总评价，权重取 0.25；
# Θ/Γ/Σ/τ 四步是过程性判据，各取 0.125。此设定使 1/137 型（Φ半开+τ部分+
# Λ预警）落入移交包，而所有单步白箱的路径保留白箱资格。
W_DEFAULT: List[float] = [0.125, 0.125, 0.125, 0.125, 0.25, 0.25]

# 六步名称（顺序固定：Θ→Γ→Σ→τ→Φ→Λ，93天 §1.2 序号）
STEP_NAMES = ["Θ-CP溯源", "Γ-CP度量", "Σ-CP根因", "τ-CP回滚", "Φ-CP门控", "Λ-CP预警"]

# 每步的语义级分类 → Φ_i 映射表（可执行化的判定字典）
# 合法键值：白箱类 / 灰箱类 / 关闭类各一个；非法值 raise。
STEP_PHI = {
    "theta":  {"known": PHI_WHITE, "partial": PHI_GREY, "unknown": PHI_CLOSED},
    "gamma":  {"exact": PHI_WHITE, "approx": PHI_GREY, "none": PHI_CLOSED},
    "sigma":  {"unique_verified": PHI_WHITE, "unique_claimed": PHI_GREY, "unknown": PHI_CLOSED},
    "tau":    {"full": PHI_WHITE, "partial": PHI_GREY, "none": PHI_CLOSED},
    "phi":    {"open": PHI_WHITE, "half": PHI_GREY, "closed": PHI_CLOSED},
    "lambda": {"no_warning": PHI_WHITE, "located": PHI_GREY, "fatal": PHI_CLOSED},
}

# 中英双语理由（白/灰/关 三档），供移交包与明细使用
REASON_CN = {
    "theta":  {"known": "输入维度完全已知（参考系可数）",
               "partial": "输入维度部分已知（量纲已知，数值黑箱）",
               "unknown": "输入维度未知（无参考系）"},
    "gamma":  {"exact": "信息损失可精确量化（精确代数式）",
               "approx": "信息损失仅部分可量化（跑动函数/近似）",
               "none": "信息损失不可量化"},
    "sigma":  {"unique_verified": "自由度约束可验证→输出唯一（已验证）",
               "unique_claimed": "自由度约束成立但未独立复现（待审）",
               "unknown": "自由度约束不可验证"},
    "tau":    {"full": "τ-CP 完全回滚（路径可逆，信息无损）",
               "partial": "τ-CP 部分回滚（存在不可逆段）",
               "none": "τ-CP 不可回滚（黑箱，无信息）"},
    "phi":    {"open": "Φ-CP 全开（计算路径完全透明）",
               "half": "Φ-CP 半开（存在黑箱段，白箱段+黑箱段）",
               "closed": "Φ-CP 关闭（路径整体不透明）"},
    "lambda": {"no_warning": "Λ-CP 无预警（推导必然成功）",
               "located": "Λ-CP 预警已定位（黑箱段已知，推导在此断裂）",
               "fatal": "Λ-CP 预警致命（推导必然失败，断裂位置未知）"},
}


def _step_phi(key: str, level: Any) -> float:
    """把单步的语义级分类映射为 Φ_i ∈ {1.0, 0.5, 0.0}。

    支持两种输入：语义字符串（见 STEP_PHI 键值），或直接给数值 0.0/0.5/1.0。
    语义字符串不在枚举内 / 数值不在三档内 → 抛 ValueError（不许静默降级）。
    """
    if isinstance(level, bool):
        raise ValueError(f"[{key}] 布尔值不能作为透明度档位")
    if isinstance(level, (int, float)):
        phi = float(level)
        if phi not in (PHI_WHITE, PHI_GREY, PHI_CLOSED):
            raise ValueError(f"[{key}] Φ_i 必须 ∈ {{1.0, 0.5, 0.0}}，收到 {phi!r}")
        return phi
    if not isinstance(level, str):
        raise ValueError(f"[{key}] 档位必须是语义字符串或数值，收到 {type(level).__name__}")
    table = STEP_PHI.get(key)
    if table is None:
        raise ValueError(f"[{key}] 未知步骤（合法：{'/'.join(STEP_PHI)}）")
    if level not in table:
        raise ValueError(f"[{key}] 未知档位 {level!r}（合法：{'/'.join(table)}）")
    return table[level]


def _reason(key: str, level: Any) -> str:
    """取中英理由文案（对数值档位反查第一匹配语义）。"""
    table = STEP_PHI[key]
    if isinstance(level, str):
        return REASON_CN[key][level]
    for sem, phi in table.items():
        if phi == level:
            return REASON_CN[key][sem]
    return "（未提供判定依据，按关闭处理）"


def tdp_cp(path: Dict[str, Any]) -> Dict[str, Any]:
    """TDP-CP 六步推演：对"计算路径"本身做透明度与可推导性裁定。

    参数:
        path: 计算路径描述。必含 "steps"（六步语义级分类），例：
              {
                "name": "254/255",
                "steps": {
                    "theta": "known", "gamma": "exact", "sigma": "unique_verified",
                    "tau": "full", "phi": "open", "lambda": "no_warning",
                },
                # 可选项：
                "weights": [0.125, 0.125, 0.125, 0.125, 0.25, 0.25],  # 覆盖默认权重（和=1）
                "tau_details": ["输出映射拓扑可数 → 反推内部(N-2)/总(N-1)"],  # 回滚细节
              }
              各步档位合法值见 STEP_PHI；也可直接给 1.0/0.5/0.0。

    返回:
        {
          "name": 计算路径名,
          "phi": [[w_i, phi_i], ...]（六步权重×门控值，顺序 Θ→Γ→Σ→τ→Φ→Λ）,
          "phi_total": float,
          "verdict": "白箱" | "移交",
          # 白箱时正文含 phi_detail；移交时正文含断裂点坐标/Φ_i 明细/τ 回滚结果
          "phi_detail": [{"step": 名, "w": w, "phi": Φ_i, "reason": 理由}, ...],
          "break_points": [{"step": 名, "phi": Φ_i, "hard": bool, "reason": 理由}, ...],
          "tau_rollback": {"type": "完全回滚"|"部分回滚"|"不可回滚", "details": [...]},
          "suggest": 白箱/移交的下一步建议,
        }

    判定规则（任务单 C3）：Φ_total = Σ w_i·Φ_i；≥ 0.7 → "白箱"；
    < 0.7 → "移交"，移交包 = 断裂点坐标 + Φ_i 明细 + τ 回滚结果。
    """
    if not isinstance(path, dict) or "steps" not in path:
        raise ValueError("path 必须是 dict 且含 'steps'（六步语义级分类）")
    steps = path["steps"]
    missing = [k for k in STEP_PHI if k not in steps]
    if missing:
        raise ValueError(f"steps 缺少步骤: {missing}（六步必须全部给出）")

    # 权重：显式覆盖 → 校验；缺省 → W_DEFAULT
    weights = list(W_DEFAULT)
    if "weights" in path:
        w = path["weights"]
        if not isinstance(w, (list, tuple)) or len(w) != 6:
            raise ValueError("weights 必须是长度为 6 的序列（Θ→Γ→Σ→τ→Φ→Λ）")
        weights = [float(x) for x in w]
        if abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError(f"weights 之和必须为 1.0，收到 {sum(weights):.6f}")

    keys = list(STEP_PHI.keys())
    phis = [_step_phi(k, steps[k]) for k in keys]
    phi_total = sum(wi * pi for wi, pi in zip(weights, phis))

    # 断裂点：Φ_i < 1.0 的步骤（Φ_i == 0.0 为硬断裂点）
    break_points = []
    for k, pi, wi in zip(keys, phis, weights):
        if pi < PHI_WHITE:
            break_points.append({
                "step": STEP_NAMES[keys.index(k)],
                "phi": pi,
                "hard": pi <= PHI_CLOSED,
                "reason": _reason(k, steps[k]),
            })

    # τ 回滚档（从 τ-CP 步取）
    tau_level = steps["tau"]
    if tau_level in ("full", PHI_WHITE, 1.0):
        tau_type = "完全回滚"
    elif tau_level in ("partial", PHI_GREY, 0.5):
        tau_type = "部分回滚"
    else:
        tau_type = "不可回滚"
    tau_rollback = {
        "type": tau_type,
        "details": list(path.get("tau_details", [])),
    }

    phi_detail = [
        {"step": STEP_NAMES[i], "w": weights[i], "phi": phis[i],
         "reason": _reason(k, steps[k])}
        for i, k in enumerate(keys)
    ]

    name = path.get("name", "（未命名计算路径）")
    is_white = phi_total >= PHI_THRESHOLD
    if is_white:
        verdict = "白箱"
        suggest = (f"Φ_total={phi_total:.4f} ≥ {PHI_THRESHOLD}：计算路径透明，"
                   f"白箱段可推（τ-CP {tau_type}，无移交）")
    else:
        verdict = "移交"
        hard_cnt = sum(1 for b in break_points if b["hard"])
        suggest = (f"Φ_total={phi_total:.4f} < {PHI_THRESHOLD}：存在黑箱段，"
                   f"移交包已给出（断裂点 {len(break_points)} 处"
                   + (f"，其中硬断裂 {hard_cnt} 处" if hard_cnt else "")
                   + f"；τ-CP {tau_type}）——白箱段可推，黑箱段不可硬给结论")

    result: Dict[str, Any] = {
        "name": name,
        "phi": [[weights[i], phis[i]] for i in range(6)],
        "phi_total": round(phi_total, 6),
        "verdict": verdict,
        "phi_detail": phi_detail,
        "tau_rollback": tau_rollback,
    }
    if not is_white:
        result["break_points"] = break_points
    result["suggest"] = suggest
    return result