# -*- coding: utf-8 -*-
"""
契约测试六项（v0.3.0 起把"能装能调"升级为"可依赖"的正式 pytest 核验）。

六项与第190天《反向方案 v1.0》验收口径一一对应，任何一项失败即阻止发版：
  1. version       —— __version__ / __spec_version__ / __article_version__ / __commit__ / CANONICAL 自洽
  2. lookup_term   —— 术语锚定表双语可查、双语完整
  3. existence_fuse—— 存在性熔断：η>LOCK_HARD 立即锁定且回滚减步；合法区不误触
  4. 跨进程 save-load —— 进程1 save_state → 新进程 load_state 返回 TianCiRuntimeV2（真跨进程，非同进程模拟）
  5. 七键          —— WarmStartPack 七字段基因子集完整，distill→save→load 往返一致
  6. 无 norm-conv  —— 落盘基因文件不含 norm/conv 瞬态键（172 只落盘基因语义）

运行：python -m pytest tests/ -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import tianci as tc  # noqa: E402

# 期望的版本契约（与 pyproject.toml / __init__.py 单一真源对账）
EXPECT_VERSION = "0.3.0"
EXPECT_SPEC_VERSION = "v7.0"
EXPECT_ARTICLE_VERSION = "v3.3.x"
EXPECT_COVERAGE = 19.5  # registry.meta.coverage_pct（25/128，如实口径不可改）

# WarmStartPack 七字段（基因子集，v0.3.0 契约）
WARMSTART_SEVEN = {
    "equilibrium", "restore_force", "amp_tail", "synapse_tail",
    "alpha", "synapse_radius", "restore_base",
}


# ── 1. version：装到的可自证 ──────────────────────────────────────────────
def test_version_contract() -> None:
    assert tc.__version__ == EXPECT_VERSION, (
        f"__version__={tc.__version__} ≠ {EXPECT_VERSION}（与 pyproject.toml 不一致）")
    assert tc.__spec_version__ == EXPECT_SPEC_VERSION
    assert tc.__article_version__ == EXPECT_ARTICLE_VERSION
    # __commit__：源码树为 None，构建注入后为 40 位 hex（与发布 tag 对齐）
    assert tc.__commit__ is None or (
        isinstance(tc.__commit__, str) and len(tc.__commit__) == 40
        and all(c in "0123456789abcdef" for c in tc.__commit__)), (
        f"__commit__ 非法：{tc.__commit__!r}")


def test_canonical_self_consistent() -> None:
    c = tc.CANONICAL
    assert c["package_version"] == EXPECT_VERSION
    assert c["spec_version"] == EXPECT_SPEC_VERSION
    assert c["article_version"] == EXPECT_ARTICLE_VERSION
    assert c["name"] == "tianci-paradigm"
    assert c["canonical_repo"].startswith("https://github.com/windsnowmichael/")
    assert "镜像" in str(c["mirror"]), "镜像必须显式标注，避免'多真源'误解"
    assert abs(c["registry_contract_coverage_pct"] - EXPECT_COVERAGE) < 1e-9


def test_registry_meta_consistent() -> None:
    reg = tc.default_registry()
    meta = reg.meta
    assert meta.get("declared_total") == 128
    assert len(reg.full_contracts()) == 25
    assert abs(float(meta.get("coverage_pct", 0)) - EXPECT_COVERAGE) < 1e-9
    audit = reg.audit()
    assert not audit.get("full_contracts_incomplete"), (
        f"注册表存在不完整契约：{audit.get('full_contracts_incomplete')}")
    assert audit.get("declared_total") == 128
    assert audit.get("contract_count") == 25


# ── 2. lookup_term：术语锚定表可查 ────────────────────────────────────────
def test_lookup_term_bilingual() -> None:
    t = tc.lookup_term("TC-SYS-003")
    assert t is not None
    assert t["zh"] == "暖启动"
    assert t["en"] == "warm start"
    assert "definition" in t, "术语条必须带定义（不能只挂 id）"


def test_glossary_bilingual_complete() -> None:
    assert tc.glossary.missing_bilingual() == [], (
        f"术语缺双语：{tc.glossary.missing_bilingual()}")
    # 运行时七器官锚点（第152天）必须存在
    for anchor in ("TC-SYS-006a", "TC-SYS-006c"):
        assert tc.glossary.lookup(anchor) is not None, f"术语锚点 {anchor} 缺失"


# ── 3. existence_fuse：存在性熔断 ─────────────────────────────────────────
@pytest.mark.parametrize("eta,expect_state", [
    (tc.LOCK_HARD + 0.01, tc.S1_LOCK),   # η>LOCK_HARD 立即锁定（存在性熔断）
    (0.23, tc.S2_FLOAT),                 # 安全区 → S2悬浮（2026-08-18 实测 η=0.23）
])
def test_existence_fuse_lock(eta: float, expect_state: str) -> None:
    state, dt_new = tc.existence_fuse(eta, prev_state="S2悬浮", dt=1.0)
    assert state == expect_state, f"η={eta} 期望 {expect_state}，实际 {state}"
    if expect_state == tc.S1_LOCK:
        assert dt_new == 0.5, f"S1锁定应回滚减半（dt/2），实际 {dt_new}"
    else:
        assert dt_new == 1.0, f"{expect_state} 不应改步长，实际 {dt_new}"


def test_existence_fuse_state_machine_full() -> None:
    # η>LOCK_HARD 从任意态锁定
    s, _ = tc.existence_fuse(tc.LOCK_HARD + 0.05, prev_state="S0", dt=2.0)
    assert s == tc.S1_LOCK
    # 合法域 [0,1] 外必须拒绝（不静默降级）
    for bad_eta in (-0.1, 1.5):
        with pytest.raises(ValueError):
            tc.existence_fuse(bad_eta, prev_state="S0", dt=1.0)


# ── 4. 跨进程 save-load：真跨进程复活 ─────────────────────────────────────
def test_cross_process_save_load() -> None:
    with tempfile.TemporaryDirectory(prefix="tianci_contract_") as tmp:
        path = os.path.join(tmp, "genome.json")
        rt = tc.TianCiRuntimeV2()
        rt.heartbeat(tc.Observation(
            label="契约/跨进程", values=[30.0, 1.0, 1.0, 1.0],
            metadata={"is_external": True}))
        tc.save_state(rt, path)
        child = (
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "from tianci.genome import load_state\n"
            "rt = load_state(%r)\n"
            "assert type(rt).__name__ == 'TianCiRuntimeV2', type(rt).__name__\n"
            "hb = rt.heartbeat(__import__('tianci').Observation("
            "label='跨进程/复活', values=[30.0, 1.0, 1.0, 1.0],"
            " metadata={'is_external': True}))\n"
            "assert hb['tick'] == 1, hb['tick']\n"
            "print('CROSS_PROCESS_OK')\n"
        ) % (REPO_ROOT, path)
        proc = subprocess.run(
            [sys.executable, "-c", child],
            capture_output=True, text=True, timeout=120,
        )
        assert proc.returncode == 0 and "CROSS_PROCESS_OK" in proc.stdout, (
            f"跨进程 load_state 失败 rc={proc.returncode} "
            f"stderr={proc.stderr.strip()[:300]}")


def _populate(rt: tc.TianCiRuntimeV2, n: int = 6) -> None:
    """连续拍心跳，让 amp/synapse 历史积累（distill 的 tail 才有内容）。"""
    for i in range(n):
        rt.heartbeat(tc.Observation(
            label=f"契约/积累{i}", values=[30.0, 1.0, 1.0, 1.0],
            metadata={"is_external": True}))


# ── 5. 七键：WarmStartPack 七字段基因子集 ─────────────────────────────────
def test_warmstart_seven_fields() -> None:
    rt = tc.TianCiRuntimeV2()
    _populate(rt)
    pack = tc.distill_warm_start(rt, tail=3)
    fields = {f.name for f in pack.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    assert fields == WARMSTART_SEVEN, f"七键契约漂移：{fields ^ WARMSTART_SEVEN}"
    assert len(pack.amp_tail) == 3 and len(pack.synapse_tail) == 3
    assert pack.equilibrium is not None


def test_warmstart_save_load_roundtrip() -> None:
    with tempfile.TemporaryDirectory(prefix="tianci_warm_") as tmp:
        path = os.path.join(tmp, "warm.json")
        rt = tc.TianCiRuntimeV2()
        _populate(rt)
        pack = tc.distill_warm_start(rt, tail=4)
        tc.save_state(pack, path)
        loaded = tc.load_state(path)
        assert type(loaded).__name__ == "TianCiRuntimeV2"
        assert loaded.synapse_radius == pack.synapse_radius
        assert abs(loaded._synapse_equilibrium - pack.equilibrium) < 1e-9


# ── 6. 无 norm-conv：落盘只含基因，不含瞬态 ────────────────────────────────
def test_save_genome_no_norm_conv() -> None:
    with tempfile.TemporaryDirectory(prefix="tianci_normconv_") as tmp:
        for fn in (tc.save_state, tc.save_genome):
            path = os.path.join(tmp, f"{fn.__name__}.json")
            rt = tc.TianCiRuntimeV2()
            rt.heartbeat(tc.Observation(
                label="契约/落盘", values=[30.0, 1.0, 1.0, 1.0],
                metadata={"is_external": True}))
            fn(rt, path)
            raw = open(path, encoding="utf-8").read().lower()
            assert "norm" not in raw and "conv" not in raw, (
                f"{fn.__name__} 落盘含 norm/conv 瞬态键（172 只落盘基因语义被破坏）")
            data = json.loads(open(path, encoding="utf-8").read())
            assert "genome_version" in data, "落盘必须有 genome_version 版本标记"