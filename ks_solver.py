# -*- coding: utf-8 -*-
"""
天赐范式 · 算子流 KS 方程求解器 v2.0
用算子流重构自洽场迭代：Ξ锚定收敛目标 / Θ溯源迭代轨迹 /
GTR曲率分析收敛速度 / Λ预警异常 / τ熔断干预 / Σ量化置信度
"""
import numpy as np
import os
import argparse
import json


class KSSolverOperators:
    """封装 KS 求解过程中的天赐范式算子"""

    def __init__(self, convergence_threshold=1e-6):
        self.Ξ_target = convergence_threshold
        self.history = {"energy": [], "density_diff": [], "steps": 0}

    def Ξ_anchor(self, density_new, density_old):
        """Ξ 锚定：计算当前密度与收敛标准的偏离度"""
        diff = np.max(np.abs(density_new - density_old))
        deviation = diff / self.Ξ_target
        self.history["density_diff"].append(diff)
        return deviation, diff

    def Θ_trace(self, iteration, energy, mixing_beta):
        """Θ 溯源：记录每一步迭代的因果链"""
        record = {
            "step": iteration + 1,
            "energy": energy,
            "mixing_beta": mixing_beta,
            "density_diff": self.history["density_diff"][-1] if self.history["density_diff"] else None
        }
        self.history["energy"].append(energy)
        self.history["steps"] = iteration + 1
        return record

    def GTR_curvature(self):
        """GTR 曲率：分析能量下降曲率，评估收敛速度"""
        if len(self.history["energy"]) < 3:
            return "initial", 0.0
        recent = self.history["energy"][-3:]
        curvature = recent[0] - 2 * recent[1] + recent[2]
        curvature = abs(curvature)
        if curvature < 1e-10:
            return "flat", curvature  # 收敛缓慢，需要更激进的混合
        elif curvature > 1e-3:
            return "steep", curvature  # 下降快，保持当前策略
        return "normal", curvature

    def Λ_alert(self, energy_history):
        """Λ 预警：检测震荡、发散"""
        if len(energy_history) < 4:
            return False, "迭代不足"
        recent = energy_history[-4:]
        oscillations = sum(1 for i in range(1, len(recent))
                          if (recent[i] - recent[i - 1]) * (recent[i - 1] - recent[i - 2]) < 0)
        if oscillations >= 2:
            return True, f"检测到震荡 (振荡次数={oscillations})"
        if max(abs(np.diff(recent))) > 10.0:
            return True, "能量剧烈波动"
        return False, "正常"

    def τ_intervention(self, alert_status, current_mixing_beta):
        """τ 熔断：异常时调整混合参数"""
        if alert_status:
            return max(0.05, current_mixing_beta * 0.7)
        return current_mixing_beta

    def Σ_uncertainty(self, grid_size, scf_converged):
        """Σ 不确定性：量化计算结果的置信度"""
        if not scf_converged:
            return 0.98
        grid_contribution = max(0, (128 - grid_size) / 128)
        basis_contribution = 0.15  # 有限基组近似误差
        return np.clip(grid_contribution + basis_contribution, 0.05, 0.98)


def run_ks_solver(init_density=0.1, grid_size=64):
    """算子流重构的 KS 方程求解主逻辑"""
    print(f"🧠 天赐范式·算子流 KS 求解器 v2.0 启动")
    print(f"   网格: {grid_size}x{grid_size}, 初始密度: {init_density}")

    # 初始化算子
    operators = KSSolverOperators(convergence_threshold=1e-6)

    # 初始密度和势能
    density = np.ones((grid_size, grid_size)) * init_density
    mixing_beta = 0.3
    max_iter = 100

    print(f"\n{'步数':<6} {'能量':<14} {'密度差':<12} {'曲率':<8} {'预警':<12} {'混合':<6}")
    print("-" * 65)

    for i in range(max_iter):
        # 构建简化的KS势能（Poisson + XC近似）
        potential = density * (1.0 + 0.5 * np.sin(np.pi * density))
        density_new = np.sqrt(np.abs(potential)) / np.pi

        # Ξ 锚定：计算偏离度
        deviation, diff = operators.Ξ_anchor(density_new, density)

        # Θ 溯源：记录迭代轨迹
        energy = np.sum(density * potential) / grid_size**2
        record = operators.Θ_trace(i, energy, mixing_beta)

        # GTR 曲率：分析收敛速度
        curvature_type, curvature_val = operators.GTR_curvature()

        # Λ 预警：检测异常
        alert, alert_msg = operators.Λ_alert(operators.history["energy"])

        # τ 熔断：异常时调整混合参数
        mixing_beta = operators.τ_intervention(alert, mixing_beta)

        # 混合密度
        density = mixing_beta * density_new + (1 - mixing_beta) * density

        # 输出迭代信息
        alert_display = f"⚠️ {alert_msg}" if alert else "✅"
        print(f"{record['step']:<6} {energy:<14.6f} {diff:<12.2e} {curvature_type:<8} {alert_display:<12} {mixing_beta:<6.3f}")

        # 收敛判断
        if diff < operators.Ξ_target:
            print(f"\n✅ 收敛！总步数: {i+1}")
            break
    else:
        print(f"\n⚠️ 未在 {max_iter} 步内收敛")

    # Σ 不确定性量化
    sigma = operators.Σ_uncertainty(grid_size, diff < operators.Ξ_target if i < max_iter-1 else False)

    # 保存结果
    os.makedirs('output', exist_ok=True)
    result = {
        "init_density": init_density,
        "grid_size": grid_size,
        "final_energy": float(operators.history["energy"][-1]),
        "total_steps": operators.history["steps"],
        "converged": diff < operators.Ξ_target,
        "uncertainty_sigma": float(sigma)
    }
    np.save(f'output/result_{init_density}.npy', density)
    with open(f'output/report_{init_density}.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"   Σ 不确定性: {sigma:.2f}")
    print(f"   结果已保存至 output/result_{init_density}.npy")
    print(f"   推演报告已保存至 output/report_{init_density}.json")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--init-density', type=float, default=0.1)
    parser.add_argument('--grid-size', type=int, default=64)
    args = parser.parse_args()
    run_ks_solver(args.init_density, args.grid_size)
