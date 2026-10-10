# -*- coding: utf-8 -*-
"""
tianci — 天赐范式（TianCi Paradigm）可 import 技术包。

第190天反向方案 v1.0 的三条硬要求在本包落地：
  1. 脱离文章载体：本地落盘 + 显式版本号 + canonical 指针（见 CANONICAL）
  2. 至少一个可 import 的模块：124 四模块（注册表/输入域/推演九步/输出域）
     + 102 天 Operator dataclass（11 字段）
  3. 术语锚定表（中英共用 ID，见 tianci.glossary）

覆盖率的如实口径（不可修改）：
  v7.0 声明 128 算子；真实契约 25 个；契约覆盖率 25/128 = 19.5%。
  剩余 103 个为半契约或仅索引。详情见 tianci.registry.Registry.audit()。
"""
from __future__ import annotations

# ---- 版本与 canonical 指针 ----
__version__ = "0.2.0"               # 本包版本（推送 PyPI/GitHub 用）
__spec_version__ = "v7.0"           # 对标的天赐范式规范版本
__title__ = "tianci-paradigm"
# CANONICAL：当前唯一权威版的指针（审计方 2026-10-10 确认，单一真源）。
# 本包是第31天 tianci-framework（19+ 原生算子）的后继；旧仓标 archived 并指向本包。
CANONICAL = {
    "name": "tianci-paradigm",
    "spec_version": "v7.0",
    "package_version": "0.2.0",
    "source": "天赐范式算子与公式大全_v7.0_终极整合扩展版.md",
    "canonical_repo": "https://github.com/windsnowmichael/tianci-framework",
    "mirror": ["AtomGit（镜像，非真源）", "第三平台（镜像，非真源）"],
    "registry_contract_coverage_pct": 19.5,
}

# ---- 模块成熟度（审计方 2026-10-10 定标，§4.2）----
# L1 公共 / L2 运行：semantic frozen（stable），可直接依赖；
# L3 生命：experimental —— 照样开放、照样可调用，语义仍在演进。
MODULE_MATURITY = {
    # L1 公共（语义冻结，可直接依赖）
    "registry": "stable",
    "operator": "stable",
    "flow": "stable",
    "dag_route": "stable",
    "glossary": "stable",
    # L2 运行（推理协议）
    "runtime_v2": "stable",
    "cp": "stable",
    "drr": "stable",
    "protocol": "stable",
    # L3 生命（experimental：照样开放、照样可调用，语义仍在演进）
    "existence": "experimental",
    "genome": "experimental",
    "consciousness": "experimental",
}

# ---- 导出 ----
from .operator import Operator, CORE_CONTRACT_FIELDS                      # noqa: E402
from .registry import Registry, default_registry                          # noqa: E402
from .runtime import Observation, TianCiRuntime                           # noqa: E402
from .runtime_v2 import (                                                 # noqa: E402
    TianCiRuntimeV2,
    WeatherAdapter,
    FinanceAdapter,
    GeneAdapter,
    WarmStartPack,
    distill_warm_start,
    warm_start_new_machine,
    migrate_and_run,
    abel_duality_test,
    abel_break,
    FLOAT_TOL,
    EPS_ABEL,
    build_cross_domain_observations,
    run_cross_domain,
    save_genome,
    load_genome,
)
from .flow import (                                                       # noqa: E402
    run_heartbeat_with_protocol,
    run_sequence_with_protocol,
    pipeline_summary,
)
from .protocol import (                                                   # noqa: E402
    LambdaLevel,
    TauVerdict,
    RState,
    run_nine_steps,
    lambda_alert,
    tau_judge,
    r_state_update,
    psi_output,
    classify_input,
    normalize_input,
    sofa_example,
)
from .dag_route import route, CASES, route_table                           # noqa: E402
from . import glossary                                                     # noqa: E402
from .glossary import lookup as lookup_term                                # noqa: E402
from .existence import (                                                   # noqa: E402
    phi_gate,
    existence_fuse,
    decide,
    LOCK_HARD,
    WARN_HI,
    WARN_LO,
    WARN_ACC,
    REL_TH,
    REL_CONS,
    S1_LOCK,
    P3_WARN,
    S2_FLOAT,
    S3_RELEASE,
)
from .genome import (                                                      # noqa: E402
    GENOME_VERSION,
    save_state,
    load_state,
)
from .cp import (                                                          # noqa: E402
    tdp_cp,
    PHI_WHITE,
    PHI_GREY,
    PHI_CLOSED,
    PHI_THRESHOLD,
    W_DEFAULT,
    STEP_NAMES,
)
from .drr import (                                                            # noqa: E402
    drr_r,
    DRR_LAYERS,
    R_ON,
    R_OFF,
    ULTIMATE_BREAK,
    COMMUTATORS,
)
from .consciousness import (                                                  # noqa: E402
    self_reflect,
    three_gate,
    alpha_beta,
    E_GATE_MAX,
    M_DIV_MAX,
    M_POI_MAX,
    U_MSIG_MAX,
    U_CV_MAX,
    L1_DELTA_THETA,
)

__all__ = [
    # 版本
    "__version__", "__spec_version__", "CANONICAL", "MODULE_MATURITY",
    # 算子契约
    "Operator", "CORE_CONTRACT_FIELDS",
    # 注册表
    "Registry", "default_registry",
    # 运行时（152）
    "Observation", "TianCiRuntime",
    # 运行时落地（152 part2）
    "TianCiRuntimeV2", "WeatherAdapter", "FinanceAdapter", "GeneAdapter",
    "WarmStartPack", "distill_warm_start", "warm_start_new_machine",
    "migrate_and_run", "abel_duality_test", "abel_break",
    "FLOAT_TOL", "EPS_ABEL", "build_cross_domain_observations",
    "run_cross_domain",
    # 九步心跳主链路（152 + 124 缝合）
    "run_heartbeat_with_protocol", "run_sequence_with_protocol", "pipeline_summary",
    # 推演协议（124）
    "LambdaLevel", "TauVerdict", "RState",
    "run_nine_steps", "lambda_alert", "tau_judge", "r_state_update", "psi_output",
    "classify_input", "normalize_input", "sofa_example",
    # DAG 决策树（102）
    "route", "CASES", "route_table",
    # 术语锚定表
    "glossary", "lookup_term",
    # 存在性检查与存在性熔断（138）
    "phi_gate", "existence_fuse", "decide",
    "LOCK_HARD", "WARN_HI", "WARN_LO", "WARN_ACC", "REL_TH", "REL_CONS",
    "S1_LOCK", "P3_WARN", "S2_FLOAT", "S3_RELEASE",
    # 基因持久化（172 / B5）
    "GENOME_VERSION", "save_state", "load_state", "save_genome", "load_genome",
    # TDP-CP 计算路径六步推演（92/93天，C3）
    # DRR-R 断裂段重定向（93天续/94天，C4）
    "drr_r", "DRR_LAYERS", "R_ON", "R_OFF", "ULTIMATE_BREAK", "COMMUTATORS",
    # 意识自指与三重门（141天，C5）
    "self_reflect", "three_gate", "alpha_beta",
    "E_GATE_MAX", "M_DIV_MAX", "M_POI_MAX", "U_MSIG_MAX", "U_CV_MAX",
    "L1_DELTA_THETA",
    "tdp_cp", "PHI_WHITE", "PHI_GREY", "PHI_CLOSED", "PHI_THRESHOLD",
    "W_DEFAULT", "STEP_NAMES",
]