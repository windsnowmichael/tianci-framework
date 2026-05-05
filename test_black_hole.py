# -*- coding: utf-8 -*-
"""
天赐范式 · 黑洞熔化公式元分析
用6个新算子检验早期推导
"""
import numpy as np
from tianci_new_operators import (
    meta_sigma, resilience,
    diminishing_returns,
    consistency_check, CouplingStrength, curvature_energy
)

# 物理常数
G_CONST = 6.67430e-11
c = 299792458
SOLAR_MASS = 1.989e30

# 伪牛顿势函数
def pseudo_newton_potential(r, M):
    rs = 2 * G_CONST * M / c**2
    return -G_CONST * M / (r - rs + 1e-12)

def test_black_hole():
    print("=" * 60)
    print("黑洞熔化公式元分析")
    print("=" * 60)

    # 1. 元不确定性MΣ检查
    print("\n[1] 元不确定性MΣ检查")
    
    def pot_sensitivity(data_error, model_divergence, external_shock):
        M = 10 * SOLAR_MASS
        r = 2.5 * 2 * G_CONST * M / c**2
        base = pseudo_newton_potential(r, M)
        perturbed = pseudo_newton_potential(r, M * (1 + data_error - 0.5))
        return abs(perturbed - base) / abs(base + 1e-12)

    for m in [1, 10, 100, 1e6, 1e9]:
        m_sigma = meta_sigma(pot_sensitivity, 0.1, 0.2, 0.05)
        print(f"  太阳质量倍数 {m:.0e}: MΣ={m_sigma:.4f}")

    # 2. 曲率能量C²检查
    print("\n[2] 曲率能量C²检查")
    M = 10 * SOLAR_MASS
    rs = 2 * G_CONST * M / c**2
    r_vals = np.linspace(1.01 * rs, 10 * rs, 20)
    phi_vals = [pseudo_newton_potential(r, M) for r in r_vals]

    c2_result = curvature_energy(phi_vals)
    print(f"  视界附近C²: {c2_result['curvature_energy']:.4e}")
    print(f"  接近临界点: {'是' if c2_result['approaching_critical'] else '否'}")

    # 3. 自洽性Con检查
    print("\n[3] 自洽性Con检查")
    r_inside = 0.5 * rs
    phi_inside = pseudo_newton_potential(r_inside, M)
    if phi_inside > 0:
        print("  PW势在视界内部变为正引力势——因果律可能被违反")
    else:
        print("  PW势在视界内仍保持负值")

    # 4. 边际递减δ检查
    print("\n[4] 边际递减δ检查")
    for mass_factor in [1, 10, 100, 1000]:
        M_test = mass_factor * SOLAR_MASS
        rs_test = 2 * G_CONST * M_test / c**2
        r_test = 3 * rs_test
        phi = pseudo_newton_potential(r_test, M_test)
        phi_normalized = abs(phi / (G_CONST * M_test / r_test + 1e-12))
        print(f"  M={mass_factor} Msun: 归一化势={phi_normalized:.4f} (1=纯牛顿)")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_black_hole()