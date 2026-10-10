# -*- coding: utf-8 -*-
"""
tianci.flow —— 九步心跳主链路：缝合第152天动态运行时 + 第124天推演协议。

思路：
  一个完整的心跳 = 运行时（十节器官）处理一次观测 + 协议（九步推演）给出裁定。
  本模块把两者缝成一条主链路：
    1) 把业务数据包装成 Observation（适配器层，见 runtime_v2）
    2) 喂给 TianCiRuntime.heartbeat —— 得到六维监察快照（ρ/σ/δ/λ/C²/MΣ）
    3) 把六维监察作为特征向量，喂给 protocol.run_nine_steps —— 得到 τ/L/R/Ψ
    4) 返回合并结果：运行时证据 + 协议裁定，一次心跳可审计。
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

from typing import Any, Dict, List, Optional

from .protocol import run_nine_steps
from .runtime import Observation, TianCiRuntime

__all__ = ["run_heartbeat_with_protocol", "run_sequence_with_protocol", "pipeline_summary"]

# 六维监察 -> 推演特征 的映射（监察值即偏差程度的自然度量）
MONITOR_TO_FEATURE = {
    "rho": "f_集中度",
    "sigma": "f_离散度",
    "delta": "f_偏态",
    "lambda": "f_峰均",
    "c2": "f_一致性",
    "m_sigma": "f_波动",
}


def run_heartbeat_with_protocol(
    obs: Observation,
    runtime: Optional[TianCiRuntime] = None,
    baseline: Optional[Dict[str, float]] = None,
    dag_has_cycle: bool = False,
) -> Dict[str, Any]:
    """
    单次心跳 + 协议裁定：
      heartbeat(obs) -> 六维监察 -> run_nine_steps(监察特征) -> {运行时证据, 协议裁定}

    返回结构:
      {
        "tick", "runtime": {V_total, V_amplified, equilibrium, transmitter_triggered, ...},
        "verdict": {tau, L, R_state, psi, sigma_total, ...},
        "features_used": {f_集中度: ..., ...}
      }
    """
    rt = runtime or TianCiRuntime()
    hb = rt.heartbeat(obs)

    if hb.get("blocked"):
        return {
            "tick": hb["tick"],
            "runtime": hb,
            "verdict": {"tau": "rollback", "L": "黄色", "R_state": "ACTIVE",
                        "psi": "输入被 Diode#96 拦截，未进入推演协议。", "sigma_total": None},
            "features_used": {},
        }

    # 从当次心跳里取六维监察（heartbeat 输出未直接带 monitor，需从画像取末帧）
    portrait = rt.export_portrait()
    monitor = portrait[-1]["monitor"] if portrait else {}

    features = {
        MONITOR_TO_FEATURE[k]: float(v)
        for k, v in monitor.items()
        if k in MONITOR_TO_FEATURE and isinstance(v, (int, float))
    }
    # c2 是"一致性"，偏差度量取 1-c2
    if "f_一致性" in features:
        features["f_一致性"] = round(1.0 - features["f_一致性"], 6)

    verdict = run_nine_steps(features, baseline=baseline, dag_has_cycle=dag_has_cycle)

    return {
        "tick": hb["tick"],
        "runtime": hb,
        "verdict": verdict,
        "features_used": features,
    }


def run_sequence_with_protocol(
    observations: List[Observation],
    runtime: Optional[TianCiRuntime] = None,
    baseline: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """对一组观测逐条跑 心跳+协议，返回结果列表（同一台机器一路跑到底）。"""
    rt = runtime or TianCiRuntime()
    return [run_heartbeat_with_protocol(obs, runtime=rt, baseline=baseline) for obs in observations]


def pipeline_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """对一组心跳+协议结果做汇总：ticks / 判定分布 / 熔断计数。"""
    verdicts: Dict[str, int] = {}
    ticks: List[int] = []
    blocked = 0
    transmitter = 0
    for r in results:
        ticks.append(r["tick"])
        tv = r["verdict"].get("tau")
        verdicts[tv] = verdicts.get(tv, 0) + 1
        if r["runtime"].get("blocked"):
            blocked += 1
        if r["runtime"].get("transmitter_triggered"):
            transmitter += 1
    return {
        "n": len(results),
        "ticks": ticks,
        "verdict_distribution": verdicts,
        "blocked_count": blocked,
        "transmitter_triggered_count": transmitter,
    }