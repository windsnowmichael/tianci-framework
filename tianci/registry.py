# -*- coding: utf-8 -*-
"""
tianci.registry —— 算子注册表（124 技术协议模块①）。

源：第124天《技术协议 v0.1》术模块① + v7.0《算子与公式大全》契约盘点。

如实口径（不可修改）：
  v7.0 声明 128 算子；全文档含『算子接口定义』代码块 26 处，
  其中 1 处为 §3.1 接口签名模板（回溯标题不含 # 编号），剔除后真实契约 25 个，
  契约覆盖率 = 25/128 = 19.5%。
  其余 103 个为半契约或仅索引（领域算子 29 + 补齐跨域 26 + R 算子 27 + 其余仅索引）。

数据源：tianci/data/registry.json（由 scripts/build_registry.py 生成，勿手改）。
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

import json
from importlib import resources
from typing import Any, Dict, List, Optional

from .operator import Operator


def load_registry(path: Optional[str] = None) -> Dict[str, Any]:
    """读取注册表。path 优先（测试/外部注入），否则读包内数据文件。"""
    if path is not None:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    text = resources.files("tianci.data").joinpath("registry.json").read_text(encoding="utf-8")
    return json.loads(text)


class Registry:
    """算子注册表：25 全契约 + 半契约组 + 覆盖率 + 双编号体系警示。"""

    def __init__(self, path: Optional[str] = None):
        raw = load_registry(path)
        self._raw = raw
        self.meta: Dict[str, Any] = raw["meta"]
        self.contracts: List[Operator] = [Operator.from_spec(s) for s in raw["contracts"]]
        self.semi_contracts: Dict[str, List[Operator]] = {
            key: [Operator.from_spec(s) for s in items]
            for key, items in raw.get("semi_contracts", {}).items()
        }
        self.fields: Dict[str, Any] = raw.get("fields", {})

    # ---------- 元信息 ----------
    @property
    def source(self) -> str:
        return self.meta.get("source", "")

    @property
    def declared_total(self) -> int:
        return int(self.meta.get("declared_total", 0))

    @property
    def contract_count(self) -> int:
        return len(self.contracts)

    @property
    def coverage_pct(self) -> float:
        """契约覆盖率，如实口径 19.5%。"""
        return float(self.meta.get("coverage_pct", 0.0))

    @property
    def dual_numbering_warning(self) -> str:
        return self.meta.get("dual_numbering_warning", "")

    def coverage_note(self) -> str:
        return self.meta.get("coverage_note", "")

    # ---------- 查询 ----------
    def get(self, symbol: str) -> Optional[Operator]:
        """按算子符号查询（覆盖全契约与半契约）。"""
        for op in self.contracts:
            if op.name == symbol:
                return op
        for group in self.semi_contracts.values():
            for op in group:
                if op.name == symbol:
                    return op
        return None

    def get_full(self, symbol: str) -> Optional[Operator]:
        """仅在全契约中按符号查询。"""
        for op in self.contracts:
            if op.name == symbol:
                return op
        return None

    def get_by_num(self, num: int) -> Optional[Operator]:
        """按契约块编号查询（仅全契约）。注意双编号体系：勿跨表映射。"""
        for op in self.contracts:
            if op.registry_num == num:
                return op
        return None

    def symbols(self, full_only: bool = False) -> List[str]:
        if full_only:
            return [op.name for op in self.contracts]
        names = [op.name for op in self.contracts]
        for group in self.semi_contracts.values():
            names.extend(op.name for op in group)
        return names

    def full_contracts(self) -> List[Operator]:
        return self.contracts

    def semi_contract_groups(self) -> Dict[str, List[Operator]]:
        return self.semi_contracts

    # ---------- 一致性审计 ----------
    def audit(self) -> Dict[str, Any]:
        """注册表自审：契约完整性 + 覆盖率 + 双编号警示。"""
        missing = [op.name for op in self.contracts if not op.has_full_contract()]
        group_stats = {k: len(v) for k, v in self.semi_contracts.items()}
        return {
            "declared_total": self.declared_total,
            "contract_count": self.contract_count,
            "coverage_pct": self.coverage_pct,
            "full_contracts_incomplete": missing,
            "semi_contract_groups": group_stats,
            "dual_numbering_warning": self.dual_numbering_warning,
            "coverage_note": self.coverage_note(),
        }

    def summary(self) -> Dict[str, Any]:
        return self.audit()


# ---------- 模块级默认注册表（惰性单例） ----------
_default: Optional[Registry] = None


def default_registry() -> Registry:
    global _default
    if _default is None:
        _default = Registry()
    return _default