# -*- coding: utf-8 -*-
"""
天赐范式 · 六个新原生算子（独立模块）
不修改任何已有代码，只提供新的算子接口
"""
import numpy as np
from datetime import datetime

# ========== 1. 元不确定性算子（Meta-Σ，符号：MΣ） ==========
def meta_sigma(sigma_func, data_error, model_divergence, external_shock, epsilon=0.01):
    """
    元不确定性算子：计算Σ对输入参数的敏感度
    来源：F3 Σ不确定性标准化
    """
    base = sigma_func(data_error, model_divergence, external_shock)
    grad_data = (sigma_func(data_error + epsilon, model_divergence, external_shock) - base) / epsilon
    grad_model = (sigma_func(data_error, model_divergence + epsilon, external_shock) - base) / epsilon
    grad_shock = (sigma_func(data_error, model_divergence, external_shock + epsilon) - base) / epsilon
    return np.sqrt(grad_data**2 + grad_model**2 + grad_shock**2)

# ========== 2. 弹性系数算子（Resilience，符号：ρ） ==========
def resilience(system_elasticity):
    """弹性系数算子：量化系统吸收冲击的能力，来源：F4 EBF蝴蝶效应"""
    return 1.0 - system_elasticity

def update_resilience(history_of_shocks, history_of_recoveries):
    """基于历史冲击和恢复记录，动态更新弹性系数"""
    if len(history_of_shocks) == 0:
        return 0.5
    recovery_rate = sum(history_of_recoveries) / len(history_of_recoveries)
    shock_magnitude = sum(history_of_shocks) / len(history_of_shocks)
    return np.clip(1.0 - shock_magnitude / (recovery_rate + 1e-6), 0.0, 1.0)

# ========== 3. 边际递减算子（Diminishing Returns，符号：δ） ==========
def diminishing_returns(current_input, saturation_threshold=1000):
    """边际递减算子：量化单位投入的边际回报，来源：F6 救援窗口指数衰减"""
    marginal = np.exp(-current_input / saturation_threshold) / saturation_threshold
    cumulative = 1.0 - np.exp(-current_input / saturation_threshold)
    return {
        "cumulative_effect": cumulative,
        "marginal_effect": marginal,
        "saturation_level": current_input / saturation_threshold
    }

def optimal_allocation(total_budget, tasks, saturation_thresholds):
    """基于边际递减原理的最优资源分配"""
    allocations = []
    remaining = total_budget
    for task, N0 in zip(tasks, saturation_thresholds):
        if remaining <= 0:
            allocations.append(0)
            continue
        alloc = min(remaining, N0 * 0.7)
        allocations.append(alloc)
        remaining -= alloc
    return allocations

# ========== 4. 自洽性算子（Consistency，符号：Con） ==========
def consistency_check(axiom_set, inference_rules, target_statement):
    """自洽性算子：检测推演链是否符合ZFC公理标准，来源：F2 数学毒丸公式"""
    contradictions = []
    for rule in inference_rules:
        if not rule.verify(axiom_set):
            contradictions.append(f"规则 {rule.name} 与公理集矛盾")
    for i in range(len(axiom_set)):
        for j in range(i + 1, len(axiom_set)):
            if axiom_set[i].contradicts(axiom_set[j]):
                contradictions.append(f"公理 {axiom_set[i].name} 与 {axiom_set[j].name} 矛盾")
    return {
        "consistent": len(contradictions) == 0,
        "contradictions": contradictions,
        "timestamp": str(datetime.now())
    }

# ========== 5. 耦合强度算子（Coupling Strength，符号：λ） ==========
class CouplingStrength:
    """耦合强度算子：控制逻辑判定到物理响应的转换力度，来源：F2 数学毒丸公式"""
    def __init__(self, initial_lambda=0.8):
        self.current_lambda = initial_lambda
        self.history = []

    def calibrate(self, risk_tolerance, false_alarm_rate, recent_outcomes):
        """基于反馈动态校准耦合强度"""
        if false_alarm_rate > risk_tolerance:
            self.current_lambda *= 0.9
        recent_incidents = sum(1 for o in recent_outcomes if o == "incident")
        if recent_incidents > 0 and false_alarm_rate < risk_tolerance * 0.5:
            self.current_lambda = min(1.0, self.current_lambda * 1.1)
        self.current_lambda = np.clip(self.current_lambda, 0.1, 1.0)
        self.history.append(self.current_lambda)
        return self.current_lambda

    def apply(self, control_signal):
        """应用耦合强度到控制信号"""
        return self.current_lambda * control_signal

# ========== 6. 曲率能量算子（Curvature Energy，符号：C²） ==========
def curvature_energy(energy_profile):
    """曲率能量算子：检测系统是否接近临界点，来源：F8 形式化验证V2指标"""
    e = np.array(energy_profile)
    grad = np.gradient(e)
    hessian = np.gradient(grad)
    c2 = float(np.sum(grad * hessian * grad))
    return {
        "curvature_energy": c2,
        "approaching_critical": abs(c2) > float(np.mean(np.abs(e))) * 0.1,
        "trend": "accelerating" if abs(c2) > float(np.mean(np.abs(grad))) else "stable"
    }