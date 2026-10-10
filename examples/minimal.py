# -*- coding: utf-8 -*-
"""tianci-paradigm 最小示例：5 分钟跑通算子流五件套。"""
import os
import sys

# 允许直接 `python examples/minimal.py` 运行（把包根目录加入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tianci import (
    TianCiRuntime,
    Observation,
    default_registry,
    run_nine_steps,
    run_heartbeat_with_protocol,
    route,
    glossary,
)


def main() -> None:
    # 1) 注册表：128 声明 / 25 全契约 / 覆盖率 19.5%
    reg = default_registry()
    print(f"[注册表] 声明 {reg.meta['declared_total']} 算子 | "
          f"全契约 {len(reg.full_contracts())} | 覆盖率 {reg.meta['coverage_pct']}%")

    # 2) 运行时心跳：七器官一次完整处理
    rt = TianCiRuntime()
    out = rt.heartbeat(Observation(
        label="气象/北京",
        values=[36.5, 0.45, 12.0, 2.3],  # demo values, not measured
        metadata={"is_rain": True, "is_high_temp": True},
    ))
    print(f"[心跳] tick={out['tick']} V_amp={out['V_amplified']:.2f} "
          f"发报机触发={out['transmitter_triggered']}")

    # 3) 九步推演协议
    verdict = run_nine_steps(
        {"f_Θ": 0.8, "f_Γ": 0.6, "f_Σ": 0.8},
        raw_input="长条形沙发，靠背侧高且有格挡，开放侧低且无格挡。",
    )
    print(f"[九步] τ={verdict['tau']} Λ={verdict['L']} R={verdict['R_state']}")

    # 4) 心跳 + 协议缝合流
    flow = run_heartbeat_with_protocol(
        Observation(label="基因/BRCA1", values=[55.0, 5.592, 8.0, 70.0])  # demo values, not measured
    )
    print(f"[缝合] τ={flow['verdict']['tau']} | Ψ={flow['verdict']['psi'][:24]}...")

    # 5) DAG 决策树（第102天）
    branch = route("50", "deg=20", "monitor=1.5", "yaw=10", "fb=0.9")
    print(f"[DAG] 分支={branch}")

    # 6) 术语锚定
    t = glossary.lookup("TC-INF-004")
    assert t is not None, "术语 TC-INF-004 必须存在"
    print(f"[术语] TC-INF-004 = {t['zh']} ({t['en']})")


if __name__ == "__main__":
    main()