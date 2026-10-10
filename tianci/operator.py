# -*- coding: utf-8 -*-
"""
tianci.operator —— 算子接口契约容器。

源：天赐范式第102天《最小化技术特征》v1.0 §7.1 算子接口签名（11 字段）。
判定某物是不是接口，不看标题有没有 API 三个字，看有没有
输入域 / 输出域 / 前置条件 / 后置保证 四件套（190 反向方案 AP-1 检出判据）。

本类在 11 字段之上提供五件套完整性校验，并把 registry.json 中的
契约字典转换为可 import、可校验的 Operator 实例。
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# 五件套：判定一个算子能否被当作接口调用的最小契约
CORE_CONTRACT_FIELDS = (
    "input_domain",
    "output_domain",
    "preconditions",
    "post_guarantees",
    "side_effects",
)


def _to_list(v: Any) -> List[Any]:
    """宽松转列表：兼容 registry.json 的字符串化元组列表与真正的列表。"""
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, (list, tuple)):
                return list(parsed)
        except Exception:
            pass
        parts = [p.strip() for p in s.split(";") if p.strip()]
        return parts or [s]
    return [v]


@dataclass
class Operator:
    """天赐范式算子接口（第102天 11 字段 + 溯源字段）。"""

    name: str                                   # 算子名 (Theta / Gamma / xi ...)
    version: str                                # 版本 (control / predict / inject / v2.0_original...)
    input_domain: List[Any] = field(default_factory=list)       # [(类型, 约束), ...]
    output_domain: List[Any] = field(default_factory=list)      # [(类型, 约束), ...]
    preconditions: List[str] = field(default_factory=list)      # [算子A已执行 / 状态S满足条件C ...]
    post_guarantees: List[str] = field(default_factory=list)    # [输出满足性质P / 状态转移到S' ...]
    side_effects: List[str] = field(default_factory=list)       # [修改全局状态 / 触发tau ...]
    domain_binding: str = "通用"                  # CFD / 精算 / 三体 / 通用 / ...
    complexity: str = "O(1)"                      # 计算复杂度
    numerical_stability: str = "无条件稳定"         # 条件稳定 / 无条件稳定 / 不稳定
    parallelizable: bool = False                  # 是否可并行
    # ---- 溯源字段（非接口契约，仅用于审计） ----
    contract_level: str = "full"                  # full=五件套齐全 / semi=缺件半契约
    registry_num: Optional[int] = None            # 契约块编号（v7.0 双编号体系，勿跨表映射）
    source_line: Optional[int] = None             # 源文档行号
    name_cn: Optional[str] = None                 # 中文名（如有）

    # ---------- 五件套校验 ----------
    def missing_fields(self) -> List[str]:
        return [f for f in CORE_CONTRACT_FIELDS if not getattr(self, f)]

    def has_full_contract(self) -> bool:
        return not self.missing_fields()

    def validate(self) -> Dict[str, Any]:
        """五件套校验：缺一即视为非接口（AP-1 检出判据）。"""
        missing = self.missing_fields()
        return {
            "ok": not missing,
            "missing": missing,
            "contract_level": self.contract_level,
            "is_interface": self.contract_level == "full" and not missing,
        }

    # ---------- 工厂 ----------
    @classmethod
    def from_spec(cls, spec: Dict[str, Any]) -> "Operator":
        """从 registry.json 契约字典或 102 天风格规范字典构造 Operator。"""
        def pick(*keys: str, default: Any = None) -> Any:
            for k in keys:
                if k in spec and spec[k] is not None:
                    return spec[k]
            return default

        name = pick("name", "symbol", "算子名", "id", default="")
        if not name and pick("算子名"):
            name = pick("算子名")
        version = pick("version", "版本", default="unknown")

        parallel = pick("parallelizable", "可并行性", default=False)
        if isinstance(parallel, str):
            parallel = parallel.strip().lower() in ("true", "yes", "1", "是", "可并行")

        op = cls(
            name=str(name),
            version=str(version),
            input_domain=_to_list(pick("input_domain", "输入域")),
            output_domain=_to_list(pick("output_domain", "输出域")),
            preconditions=[str(x) for x in _to_list(pick("preconditions", "前置条件"))],
            post_guarantees=[str(x) for x in _to_list(pick("post_guarantees", "后置保证"))],
            side_effects=[str(x) for x in _to_list(pick("side_effects", "副作用"))],
            domain_binding=str(pick("domain_binding", "领域绑定", default="通用")),
            complexity=str(pick("complexity", "计算复杂度", default="O(1)")),
            numerical_stability=str(pick("numerical_stability", "数值稳定性", default="无条件稳定")),
            parallelizable=bool(parallel),
            contract_level=str(pick("contract_level", default="full")),
            registry_num=pick("num", default=None),
            source_line=pick("line", default=None),
            name_cn=pick("name_cn", default=None),
        )
        return op

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "input_domain": self.input_domain,
            "output_domain": self.output_domain,
            "preconditions": self.preconditions,
            "post_guarantees": self.post_guarantees,
            "side_effects": self.side_effects,
            "domain_binding": self.domain_binding,
            "complexity": self.complexity,
            "numerical_stability": self.numerical_stability,
            "parallelizable": self.parallelizable,
            "contract_level": self.contract_level,
        }

    def summary(self) -> str:
        verdict = "五件套齐全" if self.has_full_contract() else "半契约，缺: " + ",".join(self.missing_fields())
        return f"{self.name} [{self.version}] {self.domain_binding} | {verdict}"