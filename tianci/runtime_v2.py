# -*- coding: utf-8 -*-
"""
tianci.runtime_v2 —— 动态运行时落地版（第152天第二篇 V2.1.0.0 终版）。

源：tianci_152_part2.py。本模块为可 import 版本：
  - ① 补丁回填自愈闭环（TianCiRuntimeV2）
  - ② 三业务域适配器（气象/金融/基因），证明零绑定
  - ③ 暖启动包（WarmStartPack）：画像跨域迁移、新机器继承记忆
  - ④ Abel 对偶映射验证：[Θ_ext, Θ_int] ≠ 0 的量化实验
  - ⑤ visualize：放大电路/突触调频/六维监察演化曲线（numpy/matplotlib 延迟导入）

依赖策略：本模块顶层零第三方依赖；numpy/matplotlib 仅在 visualize() 内延迟导入，
保证核心运行时（dispatching 用）可以在无科学计算环境处直接 import 与运行。
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from .runtime import Observation, TianCiRuntime

__all__ = [
    "TianCiRuntimeV2", "WeatherAdapter", "FinanceAdapter", "GeneAdapter",
    "WarmStartPack", "distill_warm_start", "warm_start_new_machine",
    "migrate_and_run", "abel_duality_test", "abel_break",
    "FLOAT_TOL", "EPS_ABEL", "build_cross_domain_observations",
]


# ─────────────────────────────────────────────
# §1 增强运行时：元引擎补丁真正回填参数（自愈闭环）
# ─────────────────────────────────────────────
class TianCiRuntimeV2(TianCiRuntime):
    """带补丁回填的增强运行时：元引擎生成的补丁真正修改机器参数。"""

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self._param_history: List[dict] = []
        self._snapshot_params("init")

    def _snapshot_params(self, tag: str) -> None:
        self._param_history.append({
            "tag": tag,
            "alpha": self.alpha,
            "synapse_radius": self.synapse_radius,
            "restore_base": self.restore_base,
            "tau_threshold": self.tau_threshold,
        })

    def _meta_engine(self, reasons: List[str], tick: int) -> List[dict]:
        patches = super()._meta_engine(reasons, tick)
        for p in patches:
            tgt = p["target"]
            if tgt == "放大电路":
                self.alpha = max(self.alpha * 0.8, 0.05)
                self.tau_threshold = min(self.tau_threshold * 1.15, 200.0)
            elif tgt == "Σ维度":
                self.synapse_radius = min(self.synapse_radius * 1.1, 100.0)
            elif tgt == "λ维度":
                self.restore_base = min(self.restore_base * 1.1, 5.0)
            elif tgt == "C²维度":
                self.threshold_c2 = max(self.threshold_c2 * 0.95, 0.1)
        if patches:
            self._snapshot_params(f"tick{tick}_self_heal")
        return patches

    def param_trajectory(self) -> List[dict]:
        return self._param_history


# ─────────────────────────────────────────────
# §2 业务域适配器：把真实业务数据转成无业务指纹的 Observation
# ─────────────────────────────────────────────
class WeatherAdapter:
    """气象域适配器：温度/湿度/风速/降雨量 → 通用信号向量。"""

    def to_observation(self, station: str, temp: float, humidity: float,
                       wind: float, rain: float) -> Observation:
        return Observation(
            label=f"气象/{station}",
            values=[temp, humidity, wind, rain],
            metadata={
                "is_rain": rain > 0.0,
                "is_high_temp": temp > 35.0,
                "is_strong_wind": wind > 10.0,
            },
        )


class FinanceAdapter:
    """金融域适配器：价格/成交量/波动率/涨跌幅 → 通用信号向量。"""

    def to_observation(self, code: str, price: float, volume: float,
                       volatility: float, change_pct: float) -> Observation:
        return Observation(
            label=f"金融/{code}",
            values=[price, volume / 1e6, volatility * 100.0, change_pct],
            metadata={
                "is_limit_up": change_pct > 9.5,
                "is_high_vol": volatility > 0.3,
                "is_flash_crash": change_pct < -5.0,
            },
        )


class GeneAdapter:
    """基因域适配器：GC含量/长度/突变率/表达水平 → 通用信号向量。"""

    def to_observation(self, gene_id: str, gc_content: float, length: float,
                       mutation_rate: float, expr_level: float) -> Observation:
        return Observation(
            label=f"基因/{gene_id}",
            values=[gc_content * 100.0, length / 1000.0, mutation_rate * 100.0, expr_level * 100.0],
            metadata={
                "is_high_gc": gc_content > 0.6,
                "is_mutated": mutation_rate > 0.05,
                "is_expressed": expr_level > 0.5,
            },
        )


def build_cross_domain_observations() -> Tuple[List[Observation], List[Observation], List[Observation]]:
    weather, finance, gene = WeatherAdapter(), FinanceAdapter(), GeneAdapter()
    weather_obs = [
        weather.to_observation("北京", 36.5, 0.45, 12.0, 2.3),
        weather.to_observation("上海", 28.0, 0.75, 5.0, 0.0),
        weather.to_observation("广州", 33.0, 0.85, 8.0, 15.0),
    ]
    finance_obs = [
        finance.to_observation("SH600000", 12.5, 1.2e6, 0.25, 3.2),
        finance.to_observation("SZ000001", 18.0, 2.0e6, 0.45, 10.1),
        finance.to_observation("SH688981", 85.0, 5.0e5, 0.80, -7.5),
    ]
    gene_obs = [
        gene.to_observation("BRCA1", 0.55, 5592.0, 0.08, 0.70),
        gene.to_observation("TP53", 0.62, 1181.0, 0.12, 0.90),
        gene.to_observation("EGFR", 0.48, 1210.0, 0.03, 0.20),
    ]
    return weather_obs, finance_obs, gene_obs


def run_cross_domain() -> Tuple[TianCiRuntimeV2, List[dict]]:
    """同一台空机器吃气象/金融/基因三组饭（零绑定实证）。"""
    rt = TianCiRuntimeV2()
    w_obs, f_obs, g_obs = build_cross_domain_observations()
    results: List[dict] = []
    for obs in w_obs + f_obs + g_obs:
        results.append(rt.heartbeat(obs))
    return rt, results


# ─────────────────────────────────────────────
# §4 画像导出与跨域迁移（暖启动）
# ─────────────────────────────────────────────
@dataclass
class WarmStartPack:
    """暖启动包：从源机器画像蒸馏出的可迁移初值。"""

    equilibrium: float
    restore_force: float
    amp_tail: List[float]
    synapse_tail: List[float]
    alpha: float
    synapse_radius: float
    restore_base: float

    def summary(self) -> dict:
        return {
            "equilibrium": round(self.equilibrium, 4),
            "restore_force": round(self.restore_force, 4),
            "amp_tail_len": len(self.amp_tail),
            "synapse_tail_len": len(self.synapse_tail),
            "alpha": round(self.alpha, 4),
            "synapse_radius": round(self.synapse_radius, 4),
        }


def distill_warm_start(rt: TianCiRuntimeV2, tail: int = 5) -> WarmStartPack:
    """从源机器蒸馏暖启动包。"""
    return WarmStartPack(
        equilibrium=rt._synapse_equilibrium,
        restore_force=rt._synapse_restore_force,
        amp_tail=rt._amp_history[-tail:],
        synapse_tail=rt._synapse_trajectory[-tail:],
        alpha=rt.alpha,
        synapse_radius=rt.synapse_radius,
        restore_base=rt.restore_base,
    )


def warm_start_new_machine(pack: WarmStartPack) -> TianCiRuntimeV2:
    """用暖启动包初始化一台新机器，继承源机器的记忆与参数。"""
    rt = TianCiRuntimeV2({
        "alpha": pack.alpha,
        "synapse_radius": pack.synapse_radius,
        "restore_base": pack.restore_base,
    })
    rt._synapse_equilibrium = pack.equilibrium
    rt._synapse_restore_force = pack.restore_force
    rt._amp_history = list(pack.amp_tail)
    rt._synapse_trajectory = list(pack.synapse_tail)
    return rt


def migrate_and_run(pack: WarmStartPack, new_obs: List[Observation]) -> Tuple[TianCiRuntimeV2, List[dict]]:
    """跨域迁移：暖启动一台新机器并喂入新域信号。"""
    rt = warm_start_new_machine(pack)
    results: List[dict] = []
    for obs in new_obs:
        results.append(rt.heartbeat(obs))
    return rt, results


def save_genome(rt: Union["TianCiRuntime", WarmStartPack], path: str) -> None:
    """B5 暖启动落盘：把机器（或蒸馏包）的基因落盘为 json。

    与 C2 的 save_state 同一套实现（见 tianci.genome）：
    - 落盘基因（β 参数 / strategy 元参数 / 历史轨迹 / 平衡点）；
    - 不落盘瞬态（norm / conv / tick / portrait / 门日志 / 补丁）。
    函数内延迟导入 tianci.genome，避免模块级循环依赖。
    """
    from .genome import save_state
    save_state(rt, path)


def load_genome(cls: type, path: str) -> "TianCiRuntimeV2":
    """B5 基因复活：从 json 基因文件复活一台新机器（同一套实现）。

    复活 = 新生：tick 计数归零（首次心跳 tick=1）、portrait 为空、
    converged 重置为 True；equilibrium / restore_force / 历史记忆与落盘值一致。
    cls 参数仅占位（兼容 172 天 classmethod 签名），实际复活始终为 TianCiRuntimeV2。
    """
    from .genome import load_state
    return load_state(path)


# ─────────────────────────────────────────────
# §5 Abel 对偶映射验证：[Θ_ext, Θ_int] ≠ 0
# ─────────────────────────────────────────────
FLOAT_TOL = 1e-9          # 浮点容差，仅用于判定"是否非零"
EPS_ABEL = None            # ε_abel 未标定：第132-138天仅有定性判据，无实证标定值


def abel_break(commutator_norm: float, eps_abel: Optional[float] = EPS_ABEL) -> bool:
    """‖[Θ_ext, Θ_int]‖ ≥ ε_abel ⇒ R → EMERGENCY。

    eps_abel 为 None（未标定）时必须抛错，不得回退到 FLOAT_TOL。
    定性判据来源：第132天 Abel 对偶（两篇）+ 第138天存在性熔断（见 specs/abel-handbook.md）。
    """
    if eps_abel is None:
        raise NotImplementedError("ε_abel 未标定，不可给出 Abel 破缺结论")
    return commutator_norm >= eps_abel
def _internal_autonomous(rt: TianCiRuntimeV2) -> dict:
    """Θ_int：内部自主心跳。无外部输入，以放大电路末态（记忆）做自激励。"""
    if not rt._amp_history:
        return {"tick": 0, "potential": True, "equilibrium": 0.0, "amplified": 0.0}
    self_signal = rt._amp_history[-1]
    obs = Observation(
        label="内部自主/自激励",
        values=[self_signal, self_signal, self_signal],
        metadata={"is_internal": True, "is_external": False},
    )
    r = rt.heartbeat(obs)
    r["potential"] = False
    return r


def _external_trigger(rt: TianCiRuntimeV2, obs: Observation) -> dict:
    """Θ_ext：外部触发心跳。"""
    r = rt.heartbeat(obs)
    r["potential"] = False
    return r


def abel_duality_test(seed_obs: Observation) -> dict:
    """
    验证 [Θ_ext, Θ_int] ≠ 0。返回两顺序终态及交换子范数。
    哲学印证：零输入时内部自主处于潜在态——"我被触发故我运行"。
    """
    # 顺序A：先 Θ_ext 再 Θ_int
    rt_a = TianCiRuntimeV2()
    state_a_ext = _external_trigger(rt_a, seed_obs)
    state_a_int = _internal_autonomous(rt_a)
    final_a = rt_a._synapse_equilibrium

    # 顺序B：先 Θ_int 再 Θ_ext
    rt_b = TianCiRuntimeV2()
    state_b_int = _internal_autonomous(rt_b)
    state_b_ext = _external_trigger(rt_b, seed_obs)
    final_b = rt_b._synapse_equilibrium

    commutator = abs(final_a - final_b)
    return {
        "order_a_ext_then_int": {
            "ext": state_a_ext, "int": state_a_int, "final_equilibrium": final_a,
        },
        "order_b_int_then_ext": {
            "int": state_b_int, "ext": state_b_ext, "final_equilibrium": final_b,
        },
        "commutator_norm": commutator,
        "is_nonzero": commutator > FLOAT_TOL,   # 仅陈述"范数非零"这一事实，非破缺结论
        "eps_abel": EPS_ABEL,                   # None = 未标定
        "abel_broken": None,                    # 未标定 → 不给出破缺判定（可证伪性承诺）
        "verdict": "ε_abel 未标定，未作破缺判定",
    }


# ─────────────────────────────────────────────
# §6 可视化（numpy/matplotlib 延迟导入）
# ─────────────────────────────────────────────
def visualize(rt: TianCiRuntimeV2, save_path: str) -> None:
    """
    机器心电图三幅：放大电路 Γ(t) / 突触平衡点 x*(t) / 六维监察时序。
    需要 numpy + matplotlib，仅在调用时导入。
    """
    import numpy as np  # 延迟导入
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    amp = np.array(rt._amp_history, dtype=float)
    syn = np.array(rt._synapse_trajectory, dtype=float)
    portrait = rt.export_portrait()
    n = len(portrait)

    fig, axes = plt.subplots(3, 1, figsize=(11, 13))
    fig.suptitle("天赐范式动态运行时 V2.1.0.0 — 机器心电图", fontsize=15, fontweight="bold")

    ax1 = axes[0]
    if amp.size > 0:
        ax1.plot(range(1, amp.size + 1), amp, marker="o", color="#d62728", linewidth=2)
        ax1.set_title("放大电路 Amp#95：Γ(t) 正反馈递归演化")
        ax1.set_xlabel("心跳序号")
        ax1.set_ylabel("Γ(t)")
        ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    if syn.size > 0:
        ax2.plot(range(1, syn.size + 1), syn, marker="s", color="#1f77b4", linewidth=2)
        ax2.set_title("拉格朗日点突触 R_Lagrange：x*(t) 自动调频轨迹")
        ax2.set_xlabel("心跳序号")
        ax2.set_ylabel("x*(t)")
        ax2.grid(True, alpha=0.3)

    ax3 = axes[2]
    if n > 0:
        ticks = np.arange(1, n + 1)
        dims = ["rho", "sigma", "delta", "lambda", "c2", "m_sigma"]
        labels = ["ρ 集中度", "σ 离散度", "δ 偏态", "λ 峰均比", "C² 一致性", "MΣ 综合波动"]
        colors = ["#e377c2", "#ff7f0e", "#2ca02c", "#9467bd", "#17becf", "#8c564b"]
        for dim, lab, c in zip(dims, labels, colors):
            vals = np.array([p["monitor"].get(dim, 0.0) for p in portrait])
            ax3.plot(ticks, vals, marker=".", label=lab, color=c, linewidth=1.8)
        ax3.set_title("六维监察 Λ_Bombe：ρ/σ/δ/λ/C²/MΣ 时序")
        ax3.set_xlabel("心跳序号")
        ax3.set_ylabel("监察值")
        ax3.legend(loc="upper right", fontsize=9, ncol=3)
        ax3.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(save_path, dpi=130)
    plt.close(fig)