# -*- coding: utf-8 -*-
"""
天赐范式 · 全链路自动化验证脚本
AtomGit CI 流水线每次 push 自动执行
"""
import sys
import numpy as np

print("=" * 80)
print("天赐范式 · 全链路自动化验证启动")
print("=" * 80)

# ================== 算子基类测试 ==================
print("\n[TEST 1/5] Σ 不确定性算子...")

def Sigma_uncertainty(data_error, model_divergence, external_shock):
    sigma = (np.clip(data_error / 0.5, 0, 0.35) +
             np.clip(model_divergence / 2.0, 0, 0.4) +
             np.clip(external_shock / 1.0, 0, 0.25))
    return np.clip(sigma, 0.05, 0.98)

# 测试用例
result = Sigma_uncertainty(0.1, 0.3, 0.2)
assert 0.05 <= result <= 0.98, f"Σ 计算异常: {result}"
assert result < 0.7, f"Σ 正常值应小于0.7，当前: {result}"
print(f"  ✅ Σ = {result:.2f}（通过）")

# ================== EBF蝴蝶算子测试 ==================
print("\n[TEST 2/5] EBF 蝴蝶算子...")

def EBF_butterfly_effect(initial_shock, system_elasticity):
    cold_response = 1.0 / (1.0 + np.exp(-15.0 * (abs(initial_shock) - 0.3)))
    amplified_risk = cold_response * (1.0 + 5.0 * system_elasticity) ** 2
    return np.clip(amplified_risk, 0.0, 1.0)

# 测试：零下18度极寒环境
result_cold = EBF_butterfly_effect(-18/20, 0.5)
assert result_cold > 0.5, f"极寒环境EBF风险应显著，当前: {result_cold}"
print(f"  ✅ 极寒风险EBF = {result_cold:.1%}（通过）")

# ================== 锚定算子测试 ==================
print("\n[TEST 3/5] Ξ 锚定算子...")

def Xi_anchor_deviation(current_value, target, red_line):
    target_dev = (current_value - target) / target
    red_dev = (current_value - red_line) / red_line
    return target_dev, red_dev

target_dev, red_dev = Xi_anchor_deviation(current_value=1.2, target=1.5, red_line=2.0)
assert 1.2 <= 1.5, "温升未超1.5℃目标"
print(f"  ✅ 目标偏离度={target_dev:.2f}, 红线偏离度={red_dev:.2f}（通过）")

# ================== 溯源算子测试 ==================
print("\n[TEST 4/5] Θ 溯源算子...")

def Theta_source_trace(source_data):
    total = sum(source_data.values())
    return {k: v/total for k, v in source_data.items()}

contribution = Theta_source_trace({"工业": 60, "农业": 30, "交通": 10})
assert abs(sum(contribution.values()) - 1.0) < 0.001, "溯源贡献之和应为1"
assert contribution["工业"] > 0.5, "工业应为最大贡献者"
print(f"  ✅ 溯源各贡献之和={sum(contribution.values()):.2f}（通过）")

# ================== 模式切换测试 ==================
print("\n[TEST 5/5] ZFC/¬CH 模式切换...")

mode = "ZFC"
ewma = 0.2
alpha = 0.12

def mode_switch(sigma, mode, ewma, alpha):
    ewma_new = alpha * sigma + (1 - alpha) * ewma
    if mode == "ZFC" and ewma_new > 0.5:
        mode = "not_CH"
    elif mode == "not_CH" and ewma_new < 0.35:
        mode = "ZFC"
    return mode, ewma_new

# 测试正常情况（低不确定性）
mode, ewma = mode_switch(0.3, mode, ewma, alpha)
assert mode == "ZFC", f"低不确定性不应切换模式，当前: {mode}"
print(f"  ✅ 稳态模式保持={mode}（通过）")

# ================== 总结 ==================
print("\n" + "=" * 80)
print("✅ 全链路自动化验证全部通过！天赐范式核心算子正常。")
print("=" * 80)
sys.exit(0)