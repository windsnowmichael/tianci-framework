# -*- coding: utf-8 -*-
"""
tianci.runtime —— 天赐范式动态运行时本体（第152天第一篇 V2.0.0.3 终版）。

源：tianci_152.py（文章即机器：运行本文 = 通读本文 = 完成一次心跳）。
本模块为可 import 版本：仅依赖 math/dataclasses/typing，零第三方。

七器官：
  ① Diode#96   半导体单向导通（格式净化，不做价值判断）
  ② Φ 门阵列   与或非逻辑门（自动探测布尔条件）
  ③ Amp#95     放大电路（带记忆的正反馈）
  ④ R_Lagrange 拉格朗日点突触（动态平衡，自动调频）
  ⑤ Λ_Bombe   发报机模式（六维监察，异常即触发）
  ⑥ Meta#97    元系统生成引擎（自动回溯、自动打补丁）
  ⑦ Portrait#98 意识动力学画像（可审计、可迁移、可暖启动）
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

__all__ = ["Observation", "TianCiRuntime"]


@dataclass
class Observation:
    """外部观测 Θ_ext：进入系统的唯一端口（不绑定任何业务字段）。"""

    label: str
    values: List[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class TianCiRuntime:
    """
    天赐范式动态运行时本体。
    每一个实例都是一台独立的机器，自带完整状态，互不干扰。
    """

    def __init__(self, config: Optional[dict] = None):
        cfg = config or {}
        # ---- 可配置参数（写作模型中的“初始化”ξ） ----
        self.alpha = cfg.get("alpha", 0.3)
        self.delta_t = cfg.get("delta_t", 1)
        self.tau_threshold = cfg.get("tau_threshold", 50.0)
        self.synapse_radius = cfg.get("synapse_radius", 15.0)
        self.restore_base = cfg.get("restore_base", 1.0)
        # ---- 六维监察阈值（可配置，不写死） ----
        self.threshold_rho = cfg.get("threshold_rho", 0.7)
        self.threshold_sigma = cfg.get("threshold_sigma", 0.5)
        self.threshold_delta = cfg.get("threshold_delta", 0.8)
        self.threshold_lambda = cfg.get("threshold_lambda", 0.3)
        self.threshold_c2 = cfg.get("threshold_c2", 0.5)
        self.threshold_msigma = cfg.get("threshold_msigma", 0.4)
        # ---- 信号校验策略（默认放行负值，只拦NaN/Inf） ----
        self.reject_negative = cfg.get("reject_negative", False)
        # ---- 运行时状态（每个实例独立） ----
        self._gate_log: List[dict] = []
        self._amp_history: List[float] = []
        self._converged: bool = True
        self._synapse_equilibrium: float = 0.0
        self._synapse_restore_force: float = self.restore_base
        self._synapse_trajectory: List[float] = []
        self._portrait: List[dict] = []
        self._patches: List[dict] = []
        self._tick_counter: int = 0

    # ─────────────────────────────────────────────
    # §1 半导体单向导通（Diode#96）——净化层
    # ─────────────────────────────────────────────
    def _diode_filter(self, obs: Observation) -> Tuple[bool, str]:
        """半导体PN结：格式净化，只拦非法格式，不做价值判断"""
        if not obs.label or not obs.label.strip():
            return False, "Diode#96：空标签观测被拦截"
        if not obs.values:
            return False, "Diode#96：空向量被拦截"
        if any(math.isnan(v) or math.isinf(v) for v in obs.values):
            return False, "Diode#96：NaN/Inf信号被拦截"
        if self.reject_negative and any(v < 0 for v in obs.values):
            return False, "Diode#96：负值信号被拦截（reject_negative已开启）"
        return True, "通过"

    # ─────────────────────────────────────────────
    # §2 逻辑门阵列——Φ 算子布尔完备集
    # ─────────────────────────────────────────────
    def _gate_and(self, a: bool, b: bool) -> bool:
        result = a and b
        self._gate_log.append({"type": "AND", "in": [a, b], "out": result})
        return result

    def _gate_or(self, a: bool, b: bool) -> bool:
        result = a or b
        self._gate_log.append({"type": "OR", "in": [a, b], "out": result})
        return result

    def _gate_not(self, a: bool) -> bool:
        result = not a
        self._gate_log.append({"type": "NOT", "in": [a], "out": result})
        return result

    def _gate_xor(self, a: bool, b: bool) -> bool:
        result = a ^ b
        self._gate_log.append({"type": "XOR", "in": [a, b], "out": result})
        return result

    # ─────────────────────────────────────────────
    # §3 放大电路——Amp#95（正反馈递归）
    # ─────────────────────────────────────────────
    def _amplify(self, signal: float) -> float:
        """
        放大方程：Γ(t) = Θ(t) + α · Γ(t-Δt)
        稳定性判据：相对变化率超过阈值则截断，锁定上一状态。
        """
        feedback = self._amp_history[-self.delta_t] if len(self._amp_history) >= self.delta_t else 0.0
        output = signal + self.alpha * feedback

        if len(self._amp_history) >= 3:
            prev = abs(self._amp_history[-1])
            if prev > 1e-12:
                growth = abs(output - self._amp_history[-1]) / prev
                if growth > self.tau_threshold / 100.0:
                    self._converged = False
                    output = self._amp_history[-1]

        self._amp_history.append(output)
        return output

    # ─────────────────────────────────────────────
    # §4 拉格朗日点突触——控制不动点的动态版本
    # ─────────────────────────────────────────────
    def _synapse_update(self, signal: float) -> float:
        """
        突触调频：偏离超过半径 → 恢复力随扰动频率自动提升 → 平衡点向信号方向迁移。
        """
        deviation = abs(signal - self._synapse_equilibrium)
        if deviation > self.synapse_radius:
            freq = deviation / max(self.synapse_radius, 1e-12)
            self._synapse_restore_force = self.restore_base * (1.0 + 0.5 * math.tanh(freq - 1.0))
            step = (signal - self._synapse_equilibrium) / max(1.0 + self._synapse_restore_force, 1e-12)
            step = max(-0.3 * self.synapse_radius, min(0.3 * self.synapse_radius, step))
            self._synapse_equilibrium += step
        self._synapse_trajectory.append(self._synapse_equilibrium)
        return self._synapse_equilibrium

    # ─────────────────────────────────────────────
    # §5 六维监察——Λ_Bombe 发报机模式
    # ─────────────────────────────────────────────
    def _compute_monitor(self, values: List[float], amplified: float) -> dict:
        """六维监察快照：从信号向量本身统计推导，不依赖任何业务假设"""
        n = len(values)
        if n == 0:
            return {"rho": 0, "sigma": 0, "delta": 0, "lambda": 0, "c2": 0, "m_sigma": 0, "tau": False}

        mean_v = sum(values) / n
        total_energy = sum(v * v for v in values) + 1e-12
        rho = max(abs(v) for v in values) / total_energy

        variance = sum((v - mean_v) ** 2 for v in values) / n
        sigma = math.sqrt(variance) / (abs(mean_v) + 1e-12)

        std = math.sqrt(variance)
        delta = sum(((v - mean_v) / (std + 1e-12)) ** 3 for v in values) / n if std > 1e-12 else 0.0

        lam = max(abs(v) for v in values) / (abs(mean_v) + 1e-12)

        cv = (math.sqrt(variance) + 1e-12) / (abs(mean_v) + 1e-12)
        c2 = max(0.0, 1.0 - cv)

        m_sigma = math.sqrt(sigma ** 2 + lam ** 2)

        tau = False
        if len(self._amp_history) >= 4:
            prev = abs(self._amp_history[-2])
            if prev > 1e-12:
                tau = abs(amplified - self._amp_history[-2]) / prev > 0.5

        return {
            "rho": rho, "sigma": sigma, "delta": delta,
            "lambda": lam, "c2": c2, "m_sigma": m_sigma, "tau": tau,
        }

    def _check_transmitter(self, snapshot: dict) -> Tuple[bool, List[str]]:
        """发报机触发判定：六维任一越界 → 主动发报，附带根因。"""
        reasons = []
        if snapshot["rho"] > self.threshold_rho:
            reasons.append(f"rho={snapshot['rho']:.4f} 信号集中度过高，单分量能量占比过大")
        if snapshot["sigma"] > self.threshold_sigma:
            reasons.append(f"sigma={snapshot['sigma']:.4f} 信号离散度过高，稳定性不足")
        if abs(snapshot["delta"]) > self.threshold_delta:
            reasons.append(f"delta={snapshot['delta']:.4f} 信号偏态严重，分布不对称")
        if snapshot["lambda"] > self.threshold_lambda:
            reasons.append(f"lambda={snapshot['lambda']:.4f} 峰值均值比过高，极值突出")
        if snapshot["c2"] < self.threshold_c2:
            reasons.append(f"C2={snapshot['c2']:.4f} 信号一致性过低，结构离散")
        if snapshot["m_sigma"] > self.threshold_msigma:
            reasons.append(f"MSigma={snapshot['m_sigma']:.4f} 综合波动强度过高")
        if snapshot["tau"]:
            reasons.append("放大电路发散触发熔断保护")
        return (True, reasons) if reasons else (False, [])

    # ─────────────────────────────────────────────
    # §6 元系统生成引擎——Meta#97（自举编译）
    # ─────────────────────────────────────────────
    def _meta_engine(self, reasons: List[str], tick: int) -> List[dict]:
        """元系统自举编译：根据异常原因自动生成补丁建议"""
        new_patches = []
        for reason in reasons:
            if "rho" in reason:
                new_patches.append({"id": f"P{tick}_rho", "target": "ρ维度",
                                    "action": "降低信号集中度，补充多维度输入", "confidence": 0.75})
            elif "sigma" in reason:
                new_patches.append({"id": f"P{tick}_sigma", "target": "Σ维度",
                                    "action": "降低离散度，增加参考基准", "confidence": 0.80})
            elif "delta" in reason:
                new_patches.append({"id": f"P{tick}_delta", "target": "δ维度",
                                    "action": "平衡信号分布，减少不对称性", "confidence": 0.70})
            elif "lambda" in reason:
                new_patches.append({"id": f"P{tick}_lambda", "target": "λ维度",
                                    "action": "抑制极端值，平滑信号峰值", "confidence": 0.75})
            elif "C2" in reason:
                new_patches.append({"id": f"P{tick}_c2", "target": "C²维度",
                                    "action": "优化信号结构，提升一致性", "confidence": 0.90})
            elif "熔断" in reason:
                new_patches.append({"id": f"P{tick}_tau", "target": "放大电路",
                                    "action": "降低放大系数，扩大稳定半径", "confidence": 0.85})
            else:
                new_patches.append({"id": f"P{tick}_generic", "target": "监察层",
                                    "action": "人工复核，自动补丁置信度不足", "confidence": 0.50})
        self._patches.extend(new_patches)
        return new_patches

    # ─────────────────────────────────────────────
    # §7 意识动力学画像——Portrait#98
    # ─────────────────────────────────────────────
    def _write_portrait(self, tick: int, obs: Observation, gates: dict,
                        monitor: dict, transmitter: dict, patches: list, output: dict) -> None:
        self._portrait.append({
            "tick": tick, "label": obs.label, "input": obs.values,
            "gates": gates, "monitor": monitor, "transmitter": transmitter,
            "patches": patches, "output": output,
        })

    # ─────────────────────────────────────────────
    # §8 自指节点
    # ─────────────────────────────────────────────
    def self_status(self) -> dict:
        """自指节点：本文陈述自身当前状态"""
        return {
            "version": "V2.0.0.3",
            "tick": len(self._portrait),
            "converged": self._converged,
            "equilibrium": self._synapse_equilibrium,
            "restore_force": self._synapse_restore_force,
            "portrait_length": len(self._portrait),
            "gate_log_length": len(self._gate_log),
            "patches_count": len(self._patches),
        }

    # ─────────────────────────────────────────────
    # §9 主循环——一次完整心跳
    # ─────────────────────────────────────────────
    def heartbeat(self, obs: Observation) -> dict:
        """一次完整心跳：输入 → 半导体 → 逻辑门 → 放大 → 突触 → 监察 → 发报机 → 元引擎 → 画像 → 输出"""
        self._tick_counter += 1
        tick = self._tick_counter

        passed, msg = self._diode_filter(obs)
        if not passed:
            return {"tick": tick, "blocked": True, "reason": msg}

        bool_keys = [k for k, v in obs.metadata.items() if isinstance(v, bool)]
        gate_results = {}
        for i, k1 in enumerate(bool_keys):
            for k2 in bool_keys[i + 1:]:
                gate_results[f"AND({k1},{k2})"] = self._gate_and(obs.metadata[k1], obs.metadata[k2])
                gate_results[f"OR({k1},{k2})"] = self._gate_or(obs.metadata[k1], obs.metadata[k2])
                gate_results[f"XOR({k1},{k2})"] = self._gate_xor(obs.metadata[k1], obs.metadata[k2])
        for k in bool_keys:
            gate_results[f"NOT({k})"] = self._gate_not(obs.metadata[k])

        total_v = sum(obs.values)
        amplified = self._amplify(total_v)
        equilibrium = self._synapse_update(amplified)
        monitor = self._compute_monitor(obs.values, amplified)
        bomb_triggered, bomb_reasons = self._check_transmitter(monitor)
        meta_patches = self._meta_engine(bomb_reasons, tick) if bomb_triggered else []

        output = {
            "tick": tick, "label": obs.label,
            "V_total": total_v, "V_amplified": amplified,
            "equilibrium": equilibrium, "converged": self._converged,
            "transmitter_triggered": bomb_triggered,
            "transmitter_reasons": bomb_reasons,
            "meta_patches_count": len(meta_patches),
            "version": "V2.0.0.3",
        }

        self._write_portrait(tick, obs, gate_results, monitor,
                             {"triggered": bomb_triggered, "reasons": bomb_reasons},
                             meta_patches, output)
        return output

    # ─────────────────────────────────────────────
    # §10 工具方法：导出、重置
    # ─────────────────────────────────────────────
    def export_portrait(self) -> List[dict]:
        """导出完整意识动力学画像，可用于审计、迁移、暖启动"""
        return self._portrait

    def export_patches(self) -> List[dict]:
        """导出全部自动生成的补丁建议"""
        return self._patches

    def reset(self) -> None:
        """重置运行时状态，回到初始空机状态"""
        self.__init__({
            "alpha": self.alpha, "delta_t": self.delta_t,
            "tau_threshold": self.tau_threshold,
            "synapse_radius": self.synapse_radius,
            "restore_base": self.restore_base,
            "threshold_rho": self.threshold_rho,
            "threshold_sigma": self.threshold_sigma,
            "threshold_delta": self.threshold_delta,
            "threshold_lambda": self.threshold_lambda,
            "threshold_c2": self.threshold_c2,
            "threshold_msigma": self.threshold_msigma,
            "reject_negative": self.reject_negative,
        })