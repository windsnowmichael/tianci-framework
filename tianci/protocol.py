# -*- coding: utf-8 -*-
"""
tianci.protocol —— 第124天《技术协议 v0.1》四模块：注册表 / 输入域 / 推演协议九步 / 输出域。

本模块实现协议的可执行核心：
  - 模块③ 推演协议九步（Θ→Γ→Σ→Λ→τ→Ψ 标准工作流，直接由本文档 3.2 固化）
  - 模块② 输入域规范（可处理/不可处理输入类型 + 标准化失败路由）
  - 模块④ 输出域规范（{τ, L, R_state, Ψ描述, 日志} 标准输出）
  - 模块① 由 tianci.registry 提供（Registry 即算子注册表）

阈值（如实标注：来自理论推演而非实证标定，v0.2 可能调整）：
  Σ_total < 0.3 → 绿色（无预警）
  0.3 ≤ Σ_total < 0.6 → 黄色（关注）
  Σ_total ≥ 0.6 → 红色（预警触发）
  τ ∈ {pass, rollback, fail}；R ∈ {PASSIVE, ACTIVE, EMERGENCY}
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

import math
from enum import Enum
from typing import Any, Dict, List, Optional

from .existence import S1_LOCK, S2_FLOAT, existence_fuse  # 第138天 V1.2 门控


class LambdaLevel(str, Enum):
    GREEN = "绿色"
    YELLOW = "黄色"
    RED = "红色"


class TauVerdict(str, Enum):
    PASS = "pass"
    ROLLBACK = "rollback"
    FAIL = "fail"


class RState(str, Enum):
    PASSIVE = "PASSIVE"
    ACTIVE = "ACTIVE"
    EMERGENCY = "EMERGENCY"
    FAIL = "FAIL"


THRESHOLD_YELLOW = 0.3
THRESHOLD_RED = 0.6
SHORTCUT_DEVIATION = 0.1   # 第4步：若所有 d_i < 0.1 直接跳至第9步
SEVERE_DEVIATION = 0.7     # 第4步：任一 d_i > 0.7 触发 Λ 严重预警

# 第1步：§2.3 输入类型（可处理/不可处理）
HANDLED_INPUT_TYPES = ("文本", "实验数据", "理论陈述", "设计方案", "感官描述")
UNHANDLED_INPUT_TYPES = ("数值预测", "纯形式逻辑", "纯参数拟合", "单一因果关系断言")

# 第9步：Ψ 自指输出模版
PSI_TEMPLATE = {
    "pass": "在给定输入下，系统运行正常，未发现不可解决的Θ-Γ失配。",
    "rollback": "系统检测到Σ发散>0.3，建议检查输入是否包含未预期的异常特征。",
    "fail": "系统在给定输入下无法收敛，建议回到算子注册表检查是否有缺失算子。",
}


# ══════════════════════════════════════════════════════════
# 模块② 输入域规范
# ══════════════════════════════════════════════════════════
def classify_input(raw: Any) -> Dict[str, Any]:
    """识别输入类型并判定是否可处理。"""
    kind = type(raw).__name__
    text = str(raw)
    note = ""
    handled = True
    # 只有明确宣称数值预测/纯形式逻辑等不可处理语义才拒绝
    for ut in UNHANDLED_INPUT_TYPES:
        if ut in text:
            handled = False
            note = f"命中不可处理类型：{ut}"
            break
    return {"type": kind, "handled": handled, "note": note, "std_input": text}


def normalize_input(raw: Any) -> Dict[str, Any]:
    """第1步：输入接收与标准化。失败 → 触发 Λ 预警 → 返回 τ=rollback。"""
    c = classify_input(raw)
    if not c["handled"]:
        return {
            "step": 1, "status": "rollback",
            "reason": "标准化失败：输入无法被现有算子覆盖",
            "detail": c,
        }
    return {"step": 1, "status": "ok", "I_std": c["std_input"], "detail": c}


# ══════════════════════════════════════════════════════════
# 模块③ 推演协议九步
# ══════════════════════════════════════════════════════════
def lambda_alert(sigma_total: float) -> LambdaLevel:
    """第6步：Λ 预警等级。Σ<0.3 绿 / 0.3-0.6 黄 / ≥0.6 红。"""
    if sigma_total < THRESHOLD_YELLOW:
        return LambdaLevel.GREEN
    if sigma_total < THRESHOLD_RED:
        return LambdaLevel.YELLOW
    return LambdaLevel.RED


def tau_judge(sigma_total: float, level: LambdaLevel, dag_has_cycle: bool = False,
              red_streak: int = 0) -> TauVerdict:
    """第7步：τ 判定。"""
    if dag_has_cycle:  # 若 Con 监察发现 DAG 有环 → τ 强制降级为 fail
        return TauVerdict.FAIL
    if red_streak >= 3:  # 连续3次红色预警 → 强制 fail 分支
        return TauVerdict.FAIL
    if sigma_total < THRESHOLD_YELLOW and level == LambdaLevel.GREEN:
        return TauVerdict.PASS
    if sigma_total < THRESHOLD_RED and level == LambdaLevel.YELLOW:
        return TauVerdict.ROLLBACK
    return TauVerdict.FAIL


def r_state_update(tau: TauVerdict) -> RState:
    """第8步：R 状态机更新。"""
    if tau == TauVerdict.PASS:
        return RState.PASSIVE
    if tau == TauVerdict.ROLLBACK:
        return RState.ACTIVE
    return RState.EMERGENCY


def psi_output(tau: TauVerdict, sigma_total: float, detail: Optional[str] = None) -> str:
    """第9步：Ψ 自指输出。"""
    text = PSI_TEMPLATE[tau.value]
    if tau == TauVerdict.FAIL and detail:
        text += f"（细则：{detail}）"
    return text


def run_nine_steps(features: Dict[str, float], baseline: Optional[Dict[str, float]] = None,
                   raw_input: Any = None, dag_has_cycle: bool = False,
                   red_streak: int = 0, eta: Optional[float] = None,
                   fuse_dt: float = 1.0) -> Dict[str, Any]:
    """
    完整九步推演协议。

    参数:
        features:  第3步 Θ 提取的特征向量 F = {f_Θ, f_Γ, ...}（实数值）
        baseline:  第4步 Γ 对比用的基准（默认全 0，即特征本身即偏差）
        raw_input: 原始输入（供第1步标准化；None 则跳过标准化）
        dag_has_cycle:  第7步 Con 监察结果，True 强制 τ=fail
        red_streak: 历史连续红色预警次数（第6步异常处理）
        eta:   η 如实观测值（0~1，第138天存在性熔断门控输入）。
              τ=fail 且 eta 非 None 时触发 existence_fuse；缺省表示
              η 未观测，不量化熔断步长（如实标注，不编造）。
        fuse_dt: 存在性熔断的当前演化步长基准（无量纲约定值，默认 1.0；
                 S1锁定时按 V1.2 减半返回 dt/2）。

    返回: {τ, L, R_state, Ψ描述, 算子调用日志, 各步产物}
          τ=rollback 因输入无法映射时含 {"fuse_kind": "mapping"}（B3）；
          τ=fail 时含 {"fuse_kind": "existence", "fuse": {...}}（C1）。
    """
    log: List[dict] = []

    # ── 第1步：输入接收与标准化 ──
    if raw_input is not None:
        step1 = normalize_input(raw_input)
        log.append({"step": 1, "op": "Θ", "status": step1["status"]})
        if step1["status"] == "rollback":
            return _early_rollback(step1, log)
        I_std = step1["I_std"]
    else:
        I_std = None
        log.append({"step": 1, "op": "Θ", "status": "ok(跳过标准化)"})

    # ── 第2步：Ξ 锚定 ──
    goals = [f"检查是否存在Θ-Γ失配", f"检查τ是否应判定为{fail_fallback(features)}"]
    log.append({"step": 2, "op": "Ξ", "goals": goals})

    # ── 第3步：Θ 感知读入（特征已给定） ──
    F = dict(features)
    log.append({"step": 3, "op": "Θ", "features": F})
    if all(abs(v) < 1e-9 for v in F.values()):
        log.append({"step": 3, "warn": "特征方差≈0：Θ提取的特征无法使用，进入调试模式"})

    # ── 第4步：Γ 度量（偏差向量） ──
    base = baseline or {k: 0.0 for k in F}
    D = {k: abs(F.get(k, 0.0) - base.get(k, 0.0)) for k in set(F) | set(base)}
    log.append({"step": 4, "op": "Γ", "deviations": D})
    # 捷径：所有 d_i < 0.1 → τ初判 pass → 直接跳至第9步
    shortcut = bool(D) and all(d < SHORTCUT_DEVIATION for d in D.values())
    if shortcut:
        verdict = TauVerdict.PASS
        sigma_total = 0.0
        level = LambdaLevel.GREEN
        log.append({"step": "4→9", "op": "τ", "shortcut": True})
    else:
        # 严重偏差 > 0.7 → 触发 Λ 严重预警
        severe = any(d > SEVERE_DEVIATION for d in D.values())
        # ── 第5步：Σ 不确定性量化 ──
        n = len(D)
        sigma_total = math.sqrt(sum(d * d for d in D.values())) / math.sqrt(n) if n else 0.0
        sigma_total = min(sigma_total, 1.0)   # 归一化到 [0,1]
        log.append({"step": 5, "op": "Σ", "sigma_total": round(sigma_total, 4), "n_active": n})

        # ── 第6步：Λ 预警 ──
        level = lambda_alert(sigma_total)
        log.append({"step": 6, "op": "Λ", "level": level.value, "severe": severe})
        if severe and level == LambdaLevel.GREEN:
            log.append({"step": 6, "warn": "严重偏差但Σ未超阈值：建议人工复核"})

        # ── 第7步：τ 判定 ──
        verdict = tau_judge(sigma_total, level, dag_has_cycle=dag_has_cycle, red_streak=red_streak)
        log.append({"step": 7, "op": "τ", "verdict": verdict.value})

    # ── 第8步：R 状态机更新 ──
    r_state = r_state_update(verdict)
    log.append({"step": 8, "op": "R", "state": r_state.value})

    # ── 第9步：Ψ 自指输出 ──
    psi = psi_output(verdict, sigma_total, detail=None)
    log.append({"step": 9, "op": "Ψ", "output": psi})

    result: Dict[str, Any] = {
        "tau": verdict.value,
        "L": level.value,
        "R_state": r_state.value,
        "psi": psi,
        "sigma_total": round(sigma_total, 4),
        "I_std": I_std,
        "features": F,
        "deviations": D,
        "log": log,
    }
    # C1 接线：τ=fail → 存在性熔断（第138天 V1.2 门控）
    if verdict == TauVerdict.FAIL:
        fuse: Dict[str, Any] = {"fuse_kind": "existence"}
        if eta is not None:
            fuse_state, fuse_dt_new = existence_fuse(eta, "S0", fuse_dt)
            fuse["fuse_state"] = fuse_state
            fuse["fuse_dt_new"] = fuse_dt_new
            fuse["note"] = ("S1锁定→回滚→步长减半→在更小空间重燃"
                            if fuse_state == S1_LOCK else "处于安全区，步长保持")
        else:
            fuse["fuse_state"] = None
            fuse["note"] = "η 未观测，不量化熔断步长（如实标注）"
        result["fuse"] = fuse

    return result


def _early_rollback(step1: Dict[str, Any], log: List[dict]) -> Dict[str, Any]:
    """第1步标准化失败：触发 Λ 预警 → 返回 τ=rollback（来源：输入无法映射）。

    B3 语义补全：与存在性熔断的 rollback 同名不同义，此处来源为
    mapping（输入无法映射到任何已知算子语义域），返回 fuse_kind="mapping"。
    """
    log.append({"step": 6, "op": "Λ", "level": LambdaLevel.YELLOW.value})
    log.append({"step": 7, "op": "τ", "verdict": TauVerdict.ROLLBACK.value})
    log.append({"step": 8, "op": "R", "state": RState.ACTIVE.value})
    psi = "输入无法映射到任何已知算子语义域，退回检查（fuse_kind=mapping）。"
    log.append({"step": 9, "op": "Ψ", "output": psi})
    return {
        "tau": TauVerdict.ROLLBACK.value,
        "L": LambdaLevel.YELLOW.value,
        "R_state": RState.ACTIVE.value,
        "psi": psi,
        "sigma_total": None,
        "fuse_kind": "mapping",
        "reason": step1["reason"],
        "detail": step1.get("detail", {}),
        "log": log,
    }


def fail_fallback(features: Dict[str, float]) -> str:
    """第2步辅助：目标问题兜底文案。"""
    return "fail" if (features and max(features.values()) > 0.6) else "rollback"


# ══════════════════════════════════════════════════════════
# 输出域规范：标准输出格式
# ══════════════════════════════════════════════════════════
STANDARD_OUTPUT_KEYS = ("tau", "L", "R_state", "psi", "log")


def format_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """保证输出包含标准四件套 {τ, L, R_state, Ψ描述} + 日志。"""
    out = {k: result.get(k) for k in STANDARD_OUTPUT_KEYS}
    out["sigma_total"] = result.get("sigma_total")
    return out


# ══════════════════════════════════════════════════════════
# 最小可行协议示例（124 天 §3.3 沙发示例）
# ══════════════════════════════════════════════════════════
def sofa_example() -> Dict[str, Any]:
    """124 天 §3.3 调用示例：长条形沙发结构不对称 → 认知失稳。"""
    features = {"f_Θ": 0.8, "f_Γ": 0.6, "f_Σ": 0.8}  # 原文 F 向量
    raw = "我睡在一张长条形沙发上，靠背侧高且有格挡，开放侧低且无格挡。凌晨一点走火入魔。"
    result = run_nine_steps(features, raw_input=raw)
    return result