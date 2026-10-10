# -*- coding: utf-8 -*-
"""
tianci.genome —— 基因持久化（第172天《让基因脱离个体存活》V3.3.10.0 可执行化）。

来源：
  - D:\\九月\\20260921\\tianci_172.py（save_state/load_state：落盘基因 β/strategy/历史，
    不落瞬态 norm/conv，phase 不落盘——复活即新生，重置为 explore）
  - D:\\九月\\20260921\\genomes\\{A,B,C}_genome.json（2026-09-21 实测落盘）
  - D:\\八月\\20260823\\baby_persist.py（SQLite 跨会话存活语义：记忆持久化）

关键设计（沿用 172 天原语义，不重写逻辑）：
  1. 落盘"基因"：β 参数（alpha 等）、strategy 元参数（半径/恢复基数/六维阈值）、
     历史记忆（amp 放大电路 Γ(t) / synapse 突触轨迹 / params 参数轨迹）、
     平衡点（equilibrium）与恢复力（restore_force）。
  2. 不落盘"瞬态"：norm / conv（收敛判定）、tick 计数器、画像 portrait、门日志、
     补丁列表——复活即新生：新机器从空状态开始，首次心跳 tick=1，
     平衡点从基因恢复（验收：新进程 load 后 tick=1 且平衡点与落盘值一致）。
  3. WarmStartPack 落盘走同一套：save_state/load_state 同时接受
     TianCiRuntime 系实例与 WarmStartPack（其 7 字段恰为基因子集）。
  4. 键名规范：genome 文件键名不含 "norm" / "conv" 子串（B5 验收硬约束）。

复活语义（load_state）：
  - 用基因参数构造一台新机器（继承 β/strategy）；
  - 恢复 equilibrium / restore_force / 历史记忆（amp/synapse 尾部）；
  - tick 归零、portrait 清空、converged 置 True——"进程死亡是死亡，
    基因落盘是遗体，新进程加载是复活"，复活不继承上一进程的运行瞬态。
"""
from __future__ import annotations
MATURITY = "experimental"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

import json
import os
from typing import Any, Dict, Optional, Union

from .runtime import TianCiRuntime
from .runtime_v2 import TianCiRuntimeV2, WarmStartPack, warm_start_new_machine

__all__ = [
    "GENOME_VERSION",
    "save_state",
    "load_state",
    "save_genome",
    "load_genome",
    "GENOME_KEYS",
]

GENOME_VERSION = 1   # 基因文件格式版本


def save_state(source: Union[TianCiRuntime, WarmStartPack], path: str) -> None:
    """基因落盘：β/strategy/历史/平衡点；不落盘 norm/conv 等瞬态。

    参数:
        source: TianCiRuntime / TianCiRuntimeV2 实例，或 WarmStartPack（7 字段基因子集）。
        path:   落盘 JSON 路径（父目录必须已存在）。

    返回: None。文件键名保证不含 "norm"/"conv" 子串。
    """
    if isinstance(source, WarmStartPack):
        genome = {
            "genome_version": GENOME_VERSION,
            "kind": "warm_start_pack",
            "equilibrium": source.equilibrium,
            "restore_force": source.restore_force,
            "history": {
                "amp": list(source.amp_tail),
                "synapse": list(source.synapse_tail),
            },
            "beta": {
                "alpha": source.alpha,
                "synapse_radius": source.synapse_radius,
                "restore_base": source.restore_base,
            },
            "strategy": {},
        }
    elif isinstance(source, TianCiRuntime):
        genome = {
            "genome_version": GENOME_VERSION,
            "kind": "tianci_runtime",
            "beta": {
                "alpha": source.alpha,
                "delta_t": source.delta_t,
                "tau_threshold": source.tau_threshold,
                "synapse_radius": source.synapse_radius,
                "restore_base": source.restore_base,
            },
            "strategy": {
                "threshold_rho": source.threshold_rho,
                "threshold_sigma": source.threshold_sigma,
                "threshold_delta": source.threshold_delta,
                "threshold_lambda": source.threshold_lambda,
                "threshold_c2": source.threshold_c2,
                "threshold_msigma": source.threshold_msigma,
                "reject_negative": source.reject_negative,
            },
            "equilibrium": source._synapse_equilibrium,
            "restore_force": source._synapse_restore_force,
            "history": {
                "amp": list(getattr(source, "_amp_history", [])),
                "synapse": list(getattr(source, "_synapse_trajectory", [])),
                "params": list(getattr(source, "_param_history", [])),
            },
        }
    else:
        raise TypeError("save_state 只接受 TianCiRuntime 系实例或 WarmStartPack，收到 %s" % type(source).__name__)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(genome, f, ensure_ascii=False, indent=2)


def load_state(path: str) -> TianCiRuntimeV2:
    """从基因复活：返回一台新 T2 机器，继承基因、不继承瞬态。

    复活后：
      - tick 计数归零（首次心跳返回 tick=1）；
      - portrait / 门日志 / 补丁列表为空（运行瞬态不落盘）；
      - converged 重置为 True；
      - equilibrium / restore_force / 历史记忆与落盘值一致。

    参数:
        path: 基因 JSON 文件路径。

    返回: TianCiRuntimeV2 新实例。
    """
    if not os.path.isfile(path):
        raise FileNotFoundError("基因文件不存在：%s" % path)
    with open(path, "r", encoding="utf-8") as f:
        genome = json.load(f)

    beta = genome.get("beta", {})
    strat = genome.get("strategy", {})
    config: Dict[str, Any] = {
        "alpha": beta.get("alpha", 0.3),
        "delta_t": beta.get("delta_t", 1),
        "tau_threshold": beta.get("tau_threshold", 50.0),
        "synapse_radius": beta.get("synapse_radius", 15.0),
        "restore_base": beta.get("restore_base", 1.0),
    }
    for key in ("reject_negative", "threshold_rho", "threshold_sigma",
                "threshold_delta", "threshold_lambda", "threshold_c2",
                "threshold_msigma"):
        if key in strat:
            config[key] = strat[key]

    rt = TianCiRuntimeV2(config)
    rt._synapse_equilibrium = genome.get("equilibrium", 0.0)
    rt._synapse_restore_force = genome.get("restore_force", rt.restore_base)
    hist = genome.get("history", {})
    rt._amp_history = list(hist.get("amp", []))
    rt._synapse_trajectory = list(hist.get("synapse", []))
    if "params" in hist and hasattr(rt, "_param_history"):
        rt._param_history = list(hist.get("params", []))
    # 瞬态不恢复：tick 计数器保持 0、portrait 空、converged True（复活即新生）
    return rt


# ── B5 命名（同一套实现：save_genome/load_genome 即 save_state/load_state）──
def save_genome(rt: Union[TianCiRuntime, WarmStartPack], path: str) -> None:
    """B5 接口：落盘基因（等价 save_state）。"""
    save_state(rt, path)


def load_genome(cls: Optional[type] = None, path: Optional[str] = None) -> TianCiRuntimeV2:
    """B5 接口：从基因复活（等价 load_state）。

    兼容两种调用形式：
      - classmethod 风格：load_genome(TianCiRuntimeV2, path)
      - 函数风格：load_genome(path)
    """
    if path is None:
        if isinstance(cls, str):
            path = cls
        else:
            raise TypeError("load_genome 需要基因文件路径（支持 load_genome(cls, path) 或 load_genome(path)）")
    return load_state(path)


GENOME_KEYS = ("genome_version", "kind", "beta", "strategy", "equilibrium",
               "restore_force", "history")