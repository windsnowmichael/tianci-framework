# -*- coding: utf-8 -*-
"""跨域示例：一台机器吃气象/金融/基因三域数据 + 暖启动迁移 + Abel 对偶验证。

证明：运行时零绑定——任何业务域经适配器翻译为通用 Observation 均可处理。
"""
import os
import sys

# 允许直接 `python examples/cross_domain_demo.py` 运行（把包根目录加入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tianci import (
    Observation,
    TianCiRuntimeV2,
    abel_duality_test,
    build_cross_domain_observations,
    distill_warm_start,
    migrate_and_run,
    run_cross_domain,
)


def main() -> None:
    print("=" * 62)
    print("跨域零绑定实证：一台空机器吃三域数据")
    print("=" * 62)
    rt, results = run_cross_domain()
    for r in results:
        print(f"  tick={r['tick']:2d} | {r['label']:<16s} | "
              f"V_amp={r['V_amplified']:8.2f} | 发报机={r['transmitter_triggered']}")
    print(f"  终态平衡点 x* = {rt._synapse_equilibrium:.4f}")

    print()
    print("=" * 62)
    print("暖启动：画像蒸馏 → 新机器跨域迁移")
    print("=" * 62)
    pack = distill_warm_start(rt)
    print(f"  蒸馏包: {pack.summary()}")
    new_obs = [Observation(label="金融/SH600036", values=[15.0, 3.0, 2.5, 1.2])]  # demo values, not measured
    new_rt, migrated = migrate_and_run(pack, new_obs)
    m = migrated[0]
    print(f"  迁移后首次心跳 tick={m['tick']} 平衡点={new_rt._synapse_equilibrium:.4f}")

    print()
    print("=" * 62)
    print("Abel 对偶验证：[Θ_ext, Θ_int] ≠ 0")
    print("=" * 62)
    abel = abel_duality_test(Observation(label="Abel", values=[2.0, 2.0, 2.0]))  # demo values, not measured
    norm_note = "（非零）" if abel["is_nonzero"] else "（零）"
    print(f"  交换子范数 = {abel['commutator_norm']:.6f}{norm_note}")
    print(f"  {abel['verdict']}")


if __name__ == "__main__":
    main()