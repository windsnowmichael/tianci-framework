# -*- coding: utf-8 -*-
"""
天赐范式·全灾种危情推演引擎（完整版·与系列架构统一）
✅ 三大灾种统一框架 | ✅ 全算子深度融入（含EBF蝴蝶算子）
✅ ℋ_holo跨域耦合 | ✅ Σ不确定性全程量化 | ✅ ZFC/¬CH双模式自动切换
✅ 6图联动可视化报告 | ✅ 三场景一键运行 | ✅ 与天赐范式全系列自洽
"""
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

# ====================== 全局配置 ======================
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ====================== 核心算子基类（与系列完全统一） ======================
class CrisisBaseOperators:
    """统一算子基类——抗震、抗洪、抗疫三大场景共用，与系列基类完全对齐"""
    def __init__(self, target_value, red_line_value):
        # Ξ 锚定：目标值与红线值
        self.Ξ_target = target_value
        self.Ξ_red_line = red_line_value
        # 系统状态
        self.mode = "ZFC"
        self.ewma_sigma = 0.2
        self.alpha = 0.12
        # 初始化历史数据，避免空图
        self.history = {
            "step": [-5, -4, -3, -2, -1],
            "sigma": [0.2, 0.2, 0.2, 0.2, 0.2],
            "mode": [0, 0, 0, 0, 0]
        }
        self.step_counter = 0

    def Ξ_anchor_deviation(self, current_value):
        """Ξ 锚定算子：计算当前值与目标/红线的偏离度"""
        target_deviation = (current_value - self.Ξ_target) / self.Ξ_target
        red_line_deviation = (current_value - self.Ξ_red_line) / self.Ξ_red_line
        return target_deviation, red_line_deviation

    def Λ_deviation_warning(self, target_deviation, red_line_deviation=None):
        """Λ 偏离算子：分级预警"""
        warning_level = 0
        if red_line_deviation is not None:
            if red_line_deviation >= 0:
                warning_level = 3  # 红牌预警，突破红线
            elif red_line_deviation >= -0.2:
                warning_level = 2  # 黄牌预警，临近红线
        if target_deviation > 0 and warning_level == 0:
            warning_level = 1  # 蓝牌提示，偏离目标
        return warning_level

    def Σ_uncertainty_calc(self, data_error, model_divergence, external_shock):
        """Σ 不确定性算子：标准化输出0~1"""
        sigma = (
            np.clip(data_error / 0.5, 0, 0.35) +
            np.clip(model_divergence / 2.0, 0, 0.4) +
            np.clip(external_shock / 1.0, 0, 0.25)
        )
        return np.clip(sigma, 0.05, 0.98)

    def EBF_butterfly_effect(self, initial_shock, system_elasticity):
        """EBF 蝴蝶混沌算子：基于失温生理模型的非线性放大
        - initial_shock: 归一化初始冲击 (如 cold_temp/20)
        - system_elasticity: 系统弹性/脆弱性指标 (如 aftershock_risk*10)
        采用 Sigmoid 函数描述低温风险的非对称激增，-6℃附近风险陡升。
        """
        cold_response = 1.0 / (1.0 + np.exp(-15.0 * (abs(initial_shock) - 0.3)))
        amplified_risk = cold_response * (1.0 + 5.0 * system_elasticity) ** 2
        return np.clip(amplified_risk, 0.0, 1.0)

    def mode_switch(self, sigma):
        """ZFC/¬CH 双模式自动切换"""
        self.ewma_sigma = self.alpha * sigma + (1 - self.alpha) * self.ewma_sigma
        if self.mode == "ZFC" and self.ewma_sigma > 0.5:
            self.mode = "¬CH"
            print(f"🌟 系统跃迁到 ¬CH 非均衡应急模式 (EWMA_Σ={self.ewma_sigma:.2f})")
        elif self.mode == "¬CH" and self.ewma_sigma < 0.35:
            self.mode = "ZFC"
            print(f"🌙 系统回归 ZFC 稳态防灾模式 (EWMA_Σ={self.ewma_sigma:.2f})")
        # 记录历史
        self.history["step"].append(self.step_counter)
        self.history["sigma"].append(self.ewma_sigma)
        self.history["mode"].append(1 if self.mode == "¬CH" else 0)
        self.step_counter += 1

# ====================== 三大灾种算子模块 ======================
class EarthquakeOperators(CrisisBaseOperators):
    """地震灾害算子模块"""
    def __init__(self):
        # ✅ 修复除零错误：目标值设为3.0（有感地震阈值），红线6.0（强震阈值）
        super().__init__(target_value=3.0, red_line_value=6.0)

    def Θ_damage_trace(self, damage_data):
        """Θ 溯源算子：建筑倒塌成因解析"""
        total = sum(damage_data.values())
        if total == 0:
            return {k: 0 for k in damage_data.keys()}
        return {k: v/total for k, v in damage_data.items()}

    def GTR_aftershock_risk(self, magnitude, time_since_mainshock):
        """GTR 曲率算子：余震二次倒塌风险"""
        base_risk = 0.15 * magnitude / 10
        decay = np.exp(-time_since_mainshock / 48)
        return base_risk * decay

    def τ_search_rescue(self, hours_elapsed, rescue_force_count):
        """τ 熔断算子：72小时黄金救援窗口干预"""
        survival_base = 0.9 * np.exp(-hours_elapsed / 36)
        force_efficiency = 1 - np.exp(-rescue_force_count / 1000)
        return survival_base * force_efficiency


class FloodOperators(CrisisBaseOperators):
    """洪涝灾害算子模块"""
    def __init__(self):
        # ✅ 修复除零错误：目标值设为50（警戒水位的一半），红线100（超保证水位）
        super().__init__(target_value=50, red_line_value=100)

    def Θ_flood_trace(self, water_source):
        """Θ 溯源算子：洪水来源解析"""
        total = sum(water_source.values())
        if total == 0:
            return {k: 0 for k in water_source.keys()}
        return {k: v/total for k, v in water_source.items()}

    def GTR_levee_risk(self, water_level_exceed, levee_quality):
        """GTR 曲率算子：堤防漫顶风险"""
        base_risk = water_level_exceed / 500
        quality_factor = 1 - levee_quality
        return np.clip(base_risk * quality_factor, 0, 1)

    def τ_flood_diversion(self, exceed_ratio, population_affected):
        """τ 熔断算子：分洪干预效果"""
        diversion_effect = np.clip(exceed_ratio * 0.7, 0, 0.9)
        lives_saved = population_affected * diversion_effect
        return diversion_effect, lives_saved


class EpidemicOperators(CrisisBaseOperators):
    """疫情传播算子模块"""
    def __init__(self):
        super().__init__(target_value=0.01, red_line_value=0.05)  # 红线：5%感染率

    def Θ_transmission_trace(self, transmission_source):
        """Θ 溯源算子：传播来源解析"""
        total = sum(transmission_source.values())
        if total == 0:
            return {k: 0 for k in transmission_source.keys()}
        return {k: v/total for k, v in transmission_source.items()}

    def GTR_outbreak_curve(self, r0, intervention_level, population_density):
        """GTR 曲率算子：疫情暴发斜率（人口密度分段饱和模型）
        人口密度超过1500人/km²后，进入“拥挤饱和区”，
        新增密度的边际传播贡献下降至30%，避免极端失真。
        """
        density_factor = population_density / 1000.0
        if density_factor > 1.5:
            density_factor = 1.5 + 0.3 * (density_factor - 1.5)
        effective_r = r0 * (1.0 - intervention_level) * density_factor
        return effective_r

    def τ_lockdown_intervention(self, infection_rate, lockdown_level):
        """τ 熔断算子：管控干预效果"""
        reduction = np.clip(lockdown_level * 0.6, 0, 0.8)
        new_infection_rate = infection_rate * (1 - reduction)
        return reduction, new_infection_rate

# ====================== 全息危情推演引擎主类 ======================
class HolographicCrisisEngine:
    """全灾种统一推演引擎——三大算子模块集成ℋ_holo全息耦合"""
    def __init__(self):
        # 初始化三大灾种算子模块
        self.earthquake = EarthquakeOperators()
        self.flood = FloodOperators()
        self.epidemic = EpidemicOperators()
        # 全局状态
        self.full_result = None
        self.step_counter = 0
        self.warning_map = {
            0: "正常状态",
            1: "🔵 蓝牌提示",
            2: "🟡 黄牌预警",
            3: "⚠️ 红牌——突破安全红线"
        }

    def step(self, scenario_params):
        """全系统单步推演执行"""
        print(f"\n{'='*20} 天赐范式第29天 · 全灾种危情推演引擎 {'='*20}")
        print(f"场景假设：{scenario_params.get('scenario_name', '默认场景')}")
        print("-" * 80)

        # 初始化结果字典
        result = {}
        all_sigmas = []
        disaster_type = scenario_params.get("disaster_type", "earthquake")

        # 1. 主灾害算子流执行
        if disaster_type == "earthquake" and "earthquake" in scenario_params:
            eq = scenario_params["earthquake"]
            # 算子执行
            damage_contrib = self.earthquake.Θ_damage_trace(eq["damage_data"])
            aftershock_risk = self.earthquake.GTR_aftershock_risk(eq["magnitude"], eq["hours_elapsed"])
            _, red_dev = self.earthquake.Ξ_anchor_deviation(eq["magnitude"])
            warning_eq = self.earthquake.Λ_deviation_warning(eq["magnitude"]/6.0 - 1, red_dev)
            sigma_eq = self.earthquake.Σ_uncertainty_calc(
                eq.get("data_error", 0.1),
                eq.get("model_divergence", 0.3),
                eq.get("external_shock", 0.2)
            )
            # EBF蝴蝶算子：低温压缩救援窗口的级联风险
            cold_risk = self.earthquake.EBF_butterfly_effect(eq.get("cold_temp", 0)/20, aftershock_risk*10)
            # 模式切换
            self.earthquake.mode_switch(sigma_eq)
            # τ熔断算子：救援干预
            survival_rate = self.earthquake.τ_search_rescue(eq["hours_elapsed"], eq.get("rescue_force", 1500))
            # 结果存储
            result["earthquake"] = {
                "contribution": damage_contrib,
                "aftershock_risk": aftershock_risk,
                "sigma": sigma_eq,
                "warning_level": warning_eq,
                "survival_rate": survival_rate,
                "cold_risk": cold_risk
            }
            all_sigmas.append(sigma_eq)
            # 打印输出
            print(f"🔴 【地震算子流】")
            print(f"   Ξ 锚定：生命搜救72小时黄金窗口，震中海拔{eq.get('altitude', 0)}m")
            print(f"   Θ 溯源：建筑倒塌成因——{', '.join(f'{k}{v:.0%}' for k, v in damage_contrib.items())}")
            print(f"   GTR 曲率：震级{eq['magnitude']}→余震二次倒塌风险{aftershock_risk:.1%}")
            print(f"   EBF 蝴蝶：低温级联风险{cold_risk:.1%}，黄金救援窗口压缩")
            print(f"   Σ 不确定性：{sigma_eq:.2f}")
            print(f"   Λ 预警：{self.warning_map.get(warning_eq, '正常状态')}")
            print(f"   τ 干预：{eq.get('rescue_force', 1500)}人救援力量赶赴现场，被困人员生还率{survival_rate:.1%}")

        # 2. 洪水算子流执行
        if "flood" in scenario_params:
            fl = scenario_params["flood"]
            # 算子执行
            flood_contrib = self.flood.Θ_flood_trace(fl["water_source"])
            levee_risk = self.flood.GTR_levee_risk(fl["water_level_exceed"], fl.get("levee_quality", 0.7))
            target_dev, red_dev = self.flood.Ξ_anchor_deviation(fl["water_level_exceed"])
            warning_fl = self.flood.Λ_deviation_warning(target_dev, red_dev)
            sigma_fl = self.flood.Σ_uncertainty_calc(
                fl.get("data_error", 0.15),
                fl.get("model_divergence", 0.4),
                fl.get("external_shock", 0.3)
            )
            # EBF蝴蝶算子：单点暴雨引发山洪的级联风险
            rain_risk = self.flood.EBF_butterfly_effect(fl.get("max_rain", 0)/200, levee_risk*10)
            # 模式切换
            self.flood.mode_switch(sigma_fl)
            # τ熔断算子：分洪干预
            diversion_effect, lives_saved = self.flood.τ_flood_diversion(
                fl["water_level_exceed"]/500, fl.get("population", 50000)
            )
            # 结果存储
            result["flood"] = {
                "contribution": flood_contrib,
                "levee_risk": levee_risk,
                "sigma": sigma_fl,
                "warning_level": warning_fl,
                "diversion_effect": diversion_effect,
                "lives_saved": lives_saved,
                "rain_risk": rain_risk
            }
            all_sigmas.append(sigma_fl)
            # 打印输出
            print(f"\n🌊 【洪水算子流】")
            print(f"   Ξ 锚定：流域河道保证水位、蓄滞洪区启用阈值")
            print(f"   Θ 溯源：洪水增量——{', '.join(f'{k}{v:.0%}' for k, v in flood_contrib.items())}")
            print(f"   GTR 曲率：超限水位→堤防漫顶风险{levee_risk:.1%}")
            print(f"   EBF 蝴蝶：单点暴雨级联山洪风险{rain_risk:.1%}")
            print(f"   Σ 不确定性：{sigma_fl:.2f}")
            print(f"   Λ 预警：{self.warning_map.get(warning_fl, '正常状态')}")
            print(f"   τ 干预：分洪可降低风险{diversion_effect:.0%}，保护约{lives_saved:.0f}人")

        # 3. 疫情算子流执行
        if "epidemic" in scenario_params:
            ep = scenario_params["epidemic"]
            # 算子执行
            trans_contrib = self.epidemic.Θ_transmission_trace(ep["transmission_source"])
            effective_r = self.epidemic.GTR_outbreak_curve(
                ep.get("r0", 2.5), ep.get("intervention_level", 0.3), ep.get("pop_density", 5000)
            )
            target_dev, red_dev = self.epidemic.Ξ_anchor_deviation(ep["infection_rate"])
            warning_ep = self.epidemic.Λ_deviation_warning(target_dev, red_dev)
            sigma_ep = self.epidemic.Σ_uncertainty_calc(
                ep.get("data_error", 0.1),
                ep.get("model_divergence", 0.5),
                ep.get("external_shock", 0.2)
            )
            # EBF蝴蝶算子：单个病例引发聚集性疫情的级联风险
            outbreak_risk = self.epidemic.EBF_butterfly_effect(ep["infection_rate"]*10, effective_r/3)
            # 模式切换
            self.epidemic.mode_switch(sigma_ep)
            # τ熔断算子：管控干预
            reduction, new_rate = self.epidemic.τ_lockdown_intervention(
                ep["infection_rate"], ep.get("lockdown_level", 0.5)
            )
            # 结果存储
            result["epidemic"] = {
                "contribution": trans_contrib,
                "effective_r": effective_r,
                "sigma": sigma_ep,
                "warning_level": warning_ep,
                "reduction": reduction,
                "new_infection_rate": new_rate,
                "outbreak_risk": outbreak_risk
            }
            all_sigmas.append(sigma_ep)
            # 打印输出
            print(f"\n🏥 【疫情算子流】")
            print(f"   Ξ 锚定：感染率安全阈值1%，红线5%，当前{ep['infection_rate']:.1%}")
            print(f"   Θ 溯源：传播来源——{', '.join(f'{k}{v:.0%}' for k, v in trans_contrib.items())}")
            print(f"   GTR 曲率：有效再生数R_eff = {effective_r:.2f}")
            print(f"   EBF 蝴蝶：聚集性疫情暴发风险{outbreak_risk:.1%}")
            print(f"   Σ 不确定性：{sigma_ep:.2f}")
            print(f"   Λ 预警：{self.warning_map.get(warning_ep, '正常状态')}")
            print(f"   τ 干预：管控可降低传播{reduction:.0%}，感染率降至{new_rate:.1%}")

        # 4. ℋ_holo 全息耦合：跨灾种链式传导
        holo_chain = scenario_params.get("holo_chain", [])
        if holo_chain:
            print(f"\n🔗 【ℋ_holo 全息耦合算子——跨灾种链式传导】")
            for chain in holo_chain:
                print(f"   {chain['from']} → {chain['to']}：{chain['mechanism']}，耦合强度{chain['strength']:.2f}")

        # 5. 全局耦合风险指数
        global_sigma = np.mean(all_sigmas) if all_sigmas else 0
        print("-" * 80)
        print(f"🌐 全系统耦合风险指数 = {global_sigma:.2f}")
        if global_sigma > 0.7:
            print("⚠️  【极高风险】系统处于强非均衡状态，需立即采取干预措施")
        elif global_sigma > 0.5:
            print("ℹ️  【中等风险】系统偏离稳态，需优化调度方案")
        else:
            print("✅ 【低风险】系统处于稳态区间")

        # 存储完整结果
        self.full_result = {
            "module_result": result,
            "global_sigma": global_sigma,
            "scenario": scenario_params
        }
        self.step_counter += 1
        return self.full_result

# ====================== 可视化报告生成函数（与系列完全统一） ======================
def plot_crisis_report(engine, scenario_name="场景推演"):
    """生成天赐范式全灾种危情推演监测报告，6图联动，与系列报告格式完全统一"""
    res = engine.full_result
    if not res:
        print("无推演数据，跳过报告生成")
        return

    # 提取数据
    module_data = res["module_result"]
    sigma_data = {}
    if "earthquake" in module_data:
        sigma_data["地震模块"] = module_data["earthquake"]["sigma"]
    if "flood" in module_data:
        sigma_data["洪水模块"] = module_data["flood"]["sigma"]
    if "epidemic" in module_data:
        sigma_data["疫情模块"] = module_data["epidemic"]["sigma"]

    labels = list(sigma_data.keys())
    sigma_values = list(sigma_data.values())
    global_sigma = res["global_sigma"]

    # 模式切换历史（取主灾害模块）
    main_module = engine.earthquake if "earthquake" in module_data else engine.flood
    step_history = main_module.history["step"]
    mode_history = main_module.history["mode"]

    # 创建画布，2行3列，与系列完全统一
    fig = plt.figure(figsize=(15, 9))
    fig.suptitle(f"天赐范式·全灾种危情推演监测报告 | {scenario_name}", fontsize=16, fontweight="bold")

    # 子图1：各模块Σ不确定性对比
    ax1 = fig.add_subplot(2, 3, 1)
    colors = ['#d62728', '#1f77b4', '#ff7f0e']
    bars = ax1.bar(labels, sigma_values, color=colors[:len(labels)], alpha=0.7, edgecolor='black')
    ax1.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='高风险阈值')
    ax1.set_title("各模块Σ不确定性对比", fontsize=12)
    ax1.set_ylabel("Σ 不确定性（0~1）")
    ax1.set_ylim(0, 1)
    ax1.grid(axis='y', alpha=0.3)
    ax1.legend()
    # 数值标签
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height+0.02, f'{height:.2f}', ha='center', va='bottom')

    # 子图2：全局耦合风险指数
    ax2 = fig.add_subplot(2, 3, 2)
    risk_color = '#d62728' if global_sigma>0.7 else '#ff7f0e' if global_sigma>0.5 else '#2ca02c'
    ax2.barh(["全局风险指数"], [global_sigma], color=risk_color, height=0.5)
    ax2.axvline(x=0.5, color='orange', linestyle='--', alpha=0.7, label='中等风险阈值')
    ax2.axvline(x=0.7, color='red', linestyle='--', alpha=0.7, label='高风险阈值')
    ax2.set_xlim(0, 1)
    ax2.set_title("全系统耦合风险指数", fontsize=12)
    ax2.text(global_sigma+0.02, 0, f'{global_sigma:.2f}', va='center')
    ax2.legend()

    # 子图3：关键风险驱动因子对比
    ax3 = fig.add_subplot(2, 3, 3)
    # 从各模块提取可量化的核心风险因子
    risk_factors = {}
    if "earthquake" in module_data:
        eq = module_data["earthquake"]
        risk_factors["余震倒塌风险"] = eq.get("aftershock_risk", 0) * 100
        risk_factors["低温级联风险(EBF)"] = eq.get("cold_risk", 0) * 100
    if "flood" in module_data:
        fl = module_data["flood"]
        risk_factors["堤防漫顶风险"] = fl.get("levee_risk", 0) * 100
        risk_factors["暴雨山洪风险(EBF)"] = fl.get("rain_risk", 0) * 100
    if "epidemic" in module_data:
        ep = module_data["epidemic"]
        risk_factors["有效再生数R_eff"] = ep.get("effective_r", 0)
        risk_factors["疫情暴发风险(EBF)"] = ep.get("outbreak_risk", 0) * 100

    if risk_factors:
        factor_names = list(risk_factors.keys())
        factor_values = list(risk_factors.values())
        # 颜色编码：地震-红，洪水-蓝，疫情-橙
        factor_colors = []
        for name in factor_names:
            if "倒塌" in name or "低温" in name:
                factor_colors.append('#d62728')
            elif "堤防" in name or "暴雨" in name or "山洪" in name:
                factor_colors.append('#1f77b4')
            else:
                factor_colors.append('#ff7f0e')

        bars = ax3.barh(factor_names, factor_values, color=factor_colors, alpha=0.7, edgecolor='black')
        ax3.set_title("关键风险驱动因子对比", fontsize=12)
        ax3.set_xlabel("风险值（% / 数值）")
        ax3.grid(axis='x', alpha=0.3)
        # 加数值标签，让决策者直接读数
        for bar, val in zip(bars, factor_values):
            ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                     f'{val:.1f}', va='center', fontsize=9)
    else:
        ax3.text(0.5, 0.5, '暂无风险因子数据', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title("关键风险驱动因子对比", fontsize=12)

    # 子图4：地震建筑倒塌成因（如有）
    ax4 = fig.add_subplot(2, 3, 4)
    if "earthquake" in module_data:
        eq_data = module_data["earthquake"]["contribution"]
        ax4.pie(eq_data.values(), labels=eq_data.keys(), autopct='%1.1f%%', startangle=90)
        ax4.set_title("建筑倒塌成因占比", fontsize=12)
    elif "flood" in module_data:
        fl_data = module_data["flood"]["contribution"]
        ax4.pie(fl_data.values(), labels=fl_data.keys(), autopct='%1.1f%%', startangle=90)
        ax4.set_title("洪水来源占比", fontsize=12)
    else:
        ax4.set_title("暂无主灾害数据", fontsize=12)

    # 子图5：疫情传播来源（如有）
    ax5 = fig.add_subplot(2, 3, 5)
    if "epidemic" in module_data:
        ep_data = module_data["epidemic"]["contribution"]
        ax5.pie(ep_data.values(), labels=ep_data.keys(), autopct='%1.1f%%', startangle=90)
        ax5.set_title("疫情传播来源占比", fontsize=12)
    else:
        ax5.set_title("暂无疫情数据", fontsize=12)

    # 子图6：干预效果对比
    ax6 = fig.add_subplot(2, 3, 6)
    intervention_items = []
    intervention_values = []
    if "earthquake" in module_data:
        intervention_items.append("救援生还率")
        intervention_values.append(module_data["earthquake"]["survival_rate"]*100)
    if "flood" in module_data:
        intervention_items.append("分洪风险降低")
        intervention_values.append(module_data["flood"]["diversion_effect"]*100)
    if "epidemic" in module_data:
        intervention_items.append("传播风险降低")
        intervention_values.append(module_data["epidemic"]["reduction"]*100)

    if intervention_items:
        bars6 = ax6.bar(intervention_items, intervention_values, color='#2ca02c', alpha=0.7, edgecolor='black')
        ax6.set_title("干预措施效果对比", fontsize=12)
        ax6.set_ylabel("效果（%）")
        ax6.grid(axis='y', alpha=0.3)
        for bar in bars6:
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width()/2., height+0.5, f'{height:.1f}%', ha='center', va='bottom')
    else:
        ax6.set_title("暂无干预数据", fontsize=12)

    # 布局调整
    plt.tight_layout()
    # 保存图片
    file_name = f"tianci_crisis_report_{scenario_name.replace(' ', '_')}.png"
    plt.savefig(file_name, dpi=150, bbox_inches='tight')
    print(f"📊 全灾种危情推演监测报告已保存为 {file_name}")
    # 显示图片
    plt.show()

# ====================== 主程序：三场景一键运行 ======================
if __name__ == "__main__":
    print("🧠 天赐范式·全灾种危情推演引擎启动")
    print("=" * 80)

    # 场景一：西藏定日6.8级地震推演
    print("\n\n████ 场景一：西藏定日6.8级地震 · 高寒高海拔72小时救援推演 ████")
    earthquake_scenario = {
        "scenario_name": "西藏定日6.8级地震救援推演",
        "disaster_type": "earthquake",
        "earthquake": {
            "magnitude": 6.8,
            "altitude": 4471,
            "hours_elapsed": 5,
            "cold_temp": -18,
            "rescue_force": 12000,
            "damage_data": {"土木结构": 70, "砖木结构": 25, "框架结构": 5},
            "data_error": 0.1,
            "model_divergence": 0.3,
            "external_shock": 0.2
        },
        "flood": {
            "water_level_exceed": 200,
            "levee_quality": 0.6,
            "population": 50000,
            "max_rain": 50,
            "water_source": {"滑坡堰塞湖": 60, "上游来水": 40},
            "data_error": 0.15,
            "model_divergence": 0.4,
            "external_shock": 0.3
        },
        "epidemic": {
            "infection_rate": 0.008,
            "r0": 2.5,
            "intervention_level": 0.6,
            "pop_density": 3000,
            "lockdown_level": 0.5,
            "transmission_source": {"安置点密集度": 60, "低温免疫力下降": 25, "饮用水安全": 15},
            "data_error": 0.1,
            "model_divergence": 0.5,
            "external_shock": 0.2
        },
        "holo_chain": [
            {"from": "地震", "to": "堰塞湖", "mechanism": "滑坡堵塞河道→水位上涨→溃坝风险", "strength": 0.65},
            {"from": "地震", "to": "安置点疫情", "mechanism": "人员密集+低温→呼吸道感染风险上升", "strength": 0.45},
            {"from": "堰塞湖", "to": "下游洪水", "mechanism": "溃坝→下游乡镇被淹风险", "strength": 0.72}
        ]
    }

    engine1 = HolographicCrisisEngine()
    engine1.step(earthquake_scenario)
    plot_crisis_report(engine1, "西藏定日地震救援推演")

    # 场景二：华北极端暴雨推演
    print("\n\n████ 场景二：华北极端暴雨 · 海河流域超标准洪水推演 ████")
    flood_scenario = {
        "scenario_name": "华北极端暴雨洪水推演",
        "disaster_type": "flood",
        "flood": {
            "water_level_exceed": 400,
            "levee_quality": 0.7,
            "population": 200000,
            "max_rain": 400,
            "water_source": {"太行山前暴雨产流": 55, "水库泄洪叠加": 30, "区间汇流": 15},
            "data_error": 0.15,
            "model_divergence": 0.4,
            "external_shock": 0.3
        },
        "epidemic": {
            "infection_rate": 0.015,
            "r0": 1.8,
            "intervention_level": 0.5,
            "pop_density": 4000,
            "lockdown_level": 0.4,
            "transmission_source": {"水源污染": 50, "安置点密集": 35, "卫生条件差": 15},
            "data_error": 0.1,
            "model_divergence": 0.5,
            "external_shock": 0.2
        },
        "holo_chain": [
            {"from": "洪水", "to": "水源污染", "mechanism": "洪水淹没污水厂→水源污染→饮水安全风险", "strength": 0.55},
            {"from": "洪水", "to": "道路中断", "mechanism": "道路中断→物资运输受阻→安置点物资短缺", "strength": 0.60}
        ]
    }

    engine2 = HolographicCrisisEngine()
    engine2.step(flood_scenario)
    plot_crisis_report(engine2, "华北极端暴雨洪水推演")

    # 场景三：复合巨灾推演
    print("\n\n████ 场景三：西南7.2级地震后48小时 · 四重灾害叠加推演 ████")
    compound_scenario = {
        "scenario_name": "西南地震复合巨灾推演",
        "disaster_type": "earthquake",
        "earthquake": {
            "magnitude": 7.2,
            "altitude": 1800,
            "hours_elapsed": 48,
            "rescue_force": 2500,
            "damage_data": {"土木结构": 60, "砖木结构": 30, "框架结构": 10},
            "data_error": 0.15,
            "model_divergence": 0.4,
            "external_shock": 0.3
        },
        "flood": {
            "water_level_exceed": 350,
            "levee_quality": 0.5,
            "population": 80000,
            "max_rain": 150,
            "water_source": {"暴雨产流": 45, "堰塞湖溃决": 40, "区间汇流": 15},
            "data_error": 0.2,
            "model_divergence": 0.5,
            "external_shock": 0.35
        },
        "epidemic": {
            "infection_rate": 0.025,
            "r0": 3.0,
            "intervention_level": 0.4,
            "pop_density": 6000,
            "lockdown_level": 0.6,
            "transmission_source": {"水源泥沙污染": 45, "安置点密集": 35, "临时厕所不足": 20},
            "data_error": 0.12,
            "model_divergence": 0.55,
            "external_shock": 0.25
        },
        "holo_chain": [
            {"from": "地震", "to": "地质松动", "mechanism": "主震+余震→山体松动→暴雨触发滑坡", "strength": 0.78},
            {"from": "地质松动", "to": "山洪滑坡", "mechanism": "松散堆积体+强降雨→泥石流→安置点受威胁", "strength": 0.82},
            {"from": "地震", "to": "安置点疫情", "mechanism": "二次转移→人口密度升高→疫情传播风险翻倍", "strength": 0.65},
            {"from": "暴雨", "to": "搜救暂停", "mechanism": "暴雨峰值→搜救安全性下降→需暂停高风险区搜救", "strength": 0.75}
        ]
    }

    engine3 = HolographicCrisisEngine()
    engine3.step(compound_scenario)
    plot_crisis_report(engine3, "西南地震复合巨灾推演")

    print("\n\n✅ 全灾种三场景推演全部完成！算子即一切，一切即算子。")