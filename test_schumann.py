# -*- coding: utf-8 -*-
"""
天赐范式 · 舒曼共振公式元分析
用6个新算子检验早期推导
"""
import numpy as np
from tianci_new_operators import (
    meta_sigma, resilience,
    diminishing_returns,
    consistency_check, CouplingStrength, curvature_energy
)

def schumann_freq(L=1.0, C=1.0, Gamma=0.1, lambda_c=2.5, t=0):
    """舒曼共振频率"""
    base = 1.0 / np.sqrt(L * C)
    logic_decay = (Gamma / 2.0) * np.sin(lambda_c * t)
    return base - logic_decay

def test_schumann():
    print("=" * 60)
    print("🌍 舒曼共振公式元分析")
    print("=" * 60)

    # 1. 弹性系数ρ检查
    print("\n[1] 弹性系数ρ检查")
    for gamma in [0.05, 0.1, 0.2, 0.5, 1.0]:
        base = schumann_freq(Gamma=0)
        perturbed = schumann_freq(Gamma=gamma, t=np.pi/(2*2.5))
        disturbance = abs(perturbed - base) / base
        rho = resilience(disturbance)
        print(f"  Γ={gamma:.2f}: 频率扰动={disturbance:.4f}, 弹性系数={rho:.4f}")

    # 2. 边际递减δ检查
    print("\n[2] 边际递减δ检查")
    L_vals = np.linspace(0.5, 10, 20)
    freq_vals = [schumann_freq(L=l, Gamma=0) for l in L_vals]
    for idx in [0, 5, 10, 15]:
        dim_result = diminishing_returns(idx, 20)
        print(f"  L={L_vals[idx]:.2f}: 边际效应={dim_result['marginal_effect']:.4f}, 饱和={dim_result['saturation_level']:.2%}")

    # 3. 曲率能量C²检查
    print("\n[3] 曲率能量C²检查")
    t_vals = np.linspace(0, 10, 100)
    omega_vals = [schumann_freq(Gamma=0.5, lambda_c=2.5, t=t) for t in t_vals]
    c2_result = curvature_energy(omega_vals)
    print(f"  随时间演变C²: {c2_result['curvature_energy']:.4e}")
    print(f"  趋势: {c2_result['trend']}")

    # 4. 耦合强度λ检查
    print("\n[4] 耦合强度λ检查")
    coupler = CouplingStrength(initial_lambda=0.8)
    base_freq = schumann_freq(Gamma=0)
    for scenario in ["normal"] * 8 + ["incident"] * 2:
        new_lambda = coupler.calibrate(0.1, 0.05, [scenario])
        interrupted_freq = schumann_freq(Gamma=0.1, t=1.5)
        applied_freq = base_freq - new_lambda * (base_freq - interrupted_freq)
    print(f"  λ校准后: {new_lambda:.2f}, 应用后频率={applied_freq:.4f} vs 无干扰={base_freq:.4f}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_schumann()