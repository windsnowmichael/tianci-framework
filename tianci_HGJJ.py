# -*- coding: utf-8 -*-
"""
天赐范式·全息经济学全系统引擎（可视化终极版）
✅ 全算子深度融入 | ✅ 宏观-微观-贸易-资产全息联动 | ✅ 白盒可解释
✅ 全链路不确定性量化 | ✅ ZFC/¬CH双模式切换 | ✅ 6图联动可视化报告
✅ 自动结果分析 | ✅ 可运行可验证 | ✅ 对标AGI宝宝同款视觉效果
"""
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

# ====================== 全局配置 ======================
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ====================== 宏观经济学算子流（深度重构） ======================
class MacroEconomyOperators:
    def __init__(self, target_inflation=2.0, potential_gdp_growth=5.0):
        # Ξ 锚定：系统长期稳态基准
        self.Ξ_target_inflation = target_inflation
        self.Ξ_potential_gdp_growth = potential_gdp_growth
        # 系统状态变量
        self.mode = "ZFC"
        self.ewma_sigma = 0.2
        self.alpha = 0.12
        self.history = {"step": [], "gdp_gap": [], "sigma_inflation": [], "lambda_rate": [], "mode": []}
        self.step_counter = 0

    def Ξ_anchor(self, actual_gdp_growth):
        """Ξ 锚定算子：计算产出缺口"""
        gdp_gap = (actual_gdp_growth - self.Ξ_potential_gdp_growth) / self.Ξ_potential_gdp_growth
        return gdp_gap

    def Θ_trace(self, gdp_gap, consumption_growth, investment_growth, net_export_growth):
        """Θ 溯源算子：拆解产出缺口的三大需求贡献"""
        total_growth = consumption_growth + investment_growth + net_export_growth
        if total_growth == 0:
            return {"consumption": 0, "investment": 0, "net_export": 0}
        contribution = {
            "consumption": consumption_growth / total_growth * gdp_gap,
            "investment": investment_growth / total_growth * gdp_gap,
            "net_export": net_export_growth / total_growth * gdp_gap
        }
        return contribution

    def GTR_curvature(self, unemployment_rate, inflation_rate, history_unemp, history_infl):
        """GTR 曲率算子：计算菲利普斯曲线时变弹性"""
        if len(history_unemp) < 5:
            return 0.3
        delta_unemp = np.diff(history_unemp[-10:])
        delta_infl = np.diff(history_infl[-10:])
        if np.sum(np.abs(delta_unemp)) == 0:
            return 0.0
        elasticity = np.sum(delta_infl) / np.sum(delta_unemp)
        return -elasticity

    def Λ_deviation(self, policy_rate, gdp_gap, inflation_rate):
        """Λ 偏离算子：计算泰勒规则利率偏离度"""
        taylor_rate = 2.0 + 1.5*(inflation_rate - self.Ξ_target_inflation) + 0.5*gdp_gap*100
        deviation = policy_rate - taylor_rate
        return deviation, taylor_rate

    def τ_rollback(self, deviation, sigma):
        """τ 熔断回滚算子：模拟政策干预效果"""
        intervention = 0.0
        if abs(deviation) > 2.0 and sigma > 0.7:
            intervention = -deviation * 0.5
            print(f"⚠️  τ 强熔断：政策利率偏离{deviation:.2f}%，模拟干预{intervention:.2f}%")
        elif abs(deviation) > 1.0 and sigma > 0.5:
            intervention = -deviation * 0.2
            print(f"ℹ️  τ 弱熔断：政策利率偏离{deviation:.2f}%，模拟干预{intervention:.2f}%")
        return intervention

    def Σ_uncertainty(self, forecast_variance, survey_divergence, commodity_vol):
        """Σ 不确定性算子：标准化输出[0,1]"""
        sigma = (
            np.clip(forecast_variance / 2.0, 0, 0.4) +
            np.clip(survey_divergence / 50.0, 0, 0.35) +
            np.clip(commodity_vol / 30.0, 0, 0.25)
        )
        return np.clip(sigma, 0.05, 0.98)

    def mode_switch(self, sigma):
        """ZFC/¬CH 双模式自动切换"""
        self.ewma_sigma = self.alpha * sigma + (1 - self.alpha) * self.ewma_sigma
        if self.mode == "ZFC" and self.ewma_sigma > 0.5:
            self.mode = "¬CH"
            print(f"🌟 宏观系统跃迁到 ¬CH 非均衡模式 (EWMA_Σ={self.ewma_sigma:.2f})")
        elif self.mode == "¬CH" and self.ewma_sigma < 0.35:
            self.mode = "ZFC"
            print(f"🌙 宏观系统回归 ZFC 均衡模式 (EWMA_Σ={self.ewma_sigma:.2f})")

    def step(self, actual_gdp_growth, inflation_rate, unemployment_rate, policy_rate,
             consumption_growth, investment_growth, net_export_growth,
             forecast_variance, survey_divergence, commodity_vol,
             fed_rate_change, cn_us_spread, capital_flow, initial_shock=0.0,
             history_unemp=None, history_infl=None):
        """宏观算子流单步执行"""
        if history_unemp is None:
            history_unemp = []
        if history_infl is None:
            history_infl = []
        
        gdp_gap = self.Ξ_anchor(actual_gdp_growth)
        gap_contribution = self.Θ_trace(gdp_gap, consumption_growth, investment_growth, net_export_growth)
        phillips_elasticity = self.GTR_curvature(unemployment_rate, inflation_rate, history_unemp, history_infl)
        rate_deviation, taylor_rate = self.Λ_deviation(policy_rate, gdp_gap, inflation_rate)
        sigma = self.Σ_uncertainty(forecast_variance, survey_divergence, commodity_vol)
        self.mode_switch(sigma)
        intervention = self.τ_rollback(rate_deviation, sigma)

        self.history["step"].append(self.step_counter)
        self.history["gdp_gap"].append(gdp_gap)
        self.history["sigma_inflation"].append(sigma)
        self.history["lambda_rate"].append(rate_deviation)
        self.history["mode"].append(1 if self.mode == "¬CH" else 0)
        self.step_counter += 1

        return {
            "gdp_gap": gdp_gap,
            "gap_contribution": gap_contribution,
            "phillips_elasticity": phillips_elasticity,
            "taylor_rate": taylor_rate,
            "rate_deviation": rate_deviation,
            "sigma": sigma,
            "mode": self.mode,
            "policy_intervention": intervention,
            "history": self.history
        }

# ====================== 全息经济学全系统引擎 ======================
class HolographicEconomyEngine:
    def __init__(self):
        self.macro = MacroEconomyOperators()
        self.unemp_history = deque(maxlen=20)
        self.infl_history = deque(maxlen=20)
        self.global_sigma = 0.2
        self.step_counter = 0
        self.full_result = None  # 存储完整推演结果，用于绘图

    def step(self, scenario_params):
        """全系统单步执行"""
        print(f"\n==================== 天赐范式第29天 · 全息经济学推演 ====================")
        print(f"场景假设：美联储加息{scenario_params.get('fed_rate_change', 0)*100:.0f}BP + "
              f"{scenario_params.get('tariff_increase', 0)*100:.0f}%关税 + "
              f"房价{scenario_params.get('house_price_change', 0):+.1f}%")
        print("-" * 80)

        # 1. 国际贸易算子流
        trade_result = self._trade_operators_step(scenario_params)
        # 2. 宏观算子流（读取贸易输出）
        macro_params = self._merge_macro_params(scenario_params, trade_result)
        macro_result = self.macro.step(**macro_params,
                                          history_unemp=list(self.unemp_history),
                                          history_infl=list(self.infl_history))
        # 更新历史队列
        self.unemp_history.append(scenario_params.get("unemployment_rate", 5.2))
        self.infl_history.append(scenario_params.get("inflation_rate", 2.0) + trade_result["cpi_effect"])
        # 3. 资产算子流
        asset_result = self._asset_operators_step(scenario_params, macro_result, trade_result)
        # 4. 微观个人算子流
        micro_result = self._micro_operators_step(scenario_params, macro_result, trade_result, asset_result)
        # 5. 全局全息耦合
        self.global_sigma = (macro_result["sigma"] + trade_result["sigma_trade"] +
                             asset_result["sigma_total"] + micro_result["sigma_personal"]) / 4
        
        print("-" * 80)
        print(f"🌐 全系统全息耦合风险指数 = {self.global_sigma:.2f}")
        if self.global_sigma > 0.7:
            print("⚠️  【高风险】系统处于强非均衡状态，建议增加安全垫储备")
        elif self.global_sigma > 0.5:
            print("ℹ️  【中等风险】系统偏离稳态，需警惕不确定性传导")
        else:
            print("✅ 【低风险】系统处于稳态区间")
        
        # 存储完整结果用于绘图和分析
        self.full_result = {
            "trade": trade_result,
            "macro": macro_result,
            "asset": asset_result,
            "micro": micro_result,
            "global_sigma": self.global_sigma,
            "scenario": scenario_params
        }
        self.step_counter += 1

        # 自动输出结果分析
        self._auto_analysis()
        return self.full_result

    def _trade_operators_step(self, params):
        """国际贸易算子流"""
        tariff_increase = params.get("tariff_increase", 0.0)
        fed_rate_change = params.get("fed_rate_change", 0.0)
        geo_risk = params.get("geo_risk", 0.0)

        equilibrium_exrate = 7.2 + params.get("cny_usd_spread", 0.0) * 0.1 + fed_rate_change * 0.3
        import_price_increase = tariff_increase * 0.8
        cpi_effect = import_price_increase * params.get("import_share", 0.3)
        sigma_trade = np.clip(tariff_increase/0.25 + geo_risk/0.5 + abs(fed_rate_change)/0.5, 0.05, 0.98)

        print(f"📦 【国际贸易算子流】")
        print(f"   Ξ 均衡汇率锚定：{equilibrium_exrate:.2f}")
        print(f"   GTR 关税冲击：进口价格上涨{import_price_increase:.1%}，CPI传导效应{cpi_effect:.1%}")
        print(f"   Σ 贸易不确定性：{sigma_trade:.2f}")
        return {
            "equilibrium_exrate": equilibrium_exrate,
            "import_price_increase": import_price_increase,
            "cpi_effect": cpi_effect,
            "sigma_trade": sigma_trade
        }

    def _merge_macro_params(self, scenario_params, trade_result):
        """合并贸易输出到宏观参数"""
        return {
            "actual_gdp_growth": scenario_params.get("actual_gdp_growth", 5.0),
            "inflation_rate": scenario_params.get("inflation_rate", 2.0) + trade_result["cpi_effect"],
            "unemployment_rate": scenario_params.get("unemployment_rate", 5.2),
            "policy_rate": scenario_params.get("policy_rate", 2.0),
            "consumption_growth": scenario_params.get("consumption_growth", 6.0),
            "investment_growth": scenario_params.get("investment_growth", 4.0),
            "net_export_growth": scenario_params.get("net_export_growth", 2.0),
            "forecast_variance": scenario_params.get("forecast_variance", 1.0),
            "survey_divergence": scenario_params.get("survey_divergence", 20.0),
            "commodity_vol": scenario_params.get("commodity_vol", 10.0),
            "fed_rate_change": scenario_params.get("fed_rate_change", 0.0),
            "cn_us_spread": scenario_params.get("cny_usd_spread", 0.0),
            "capital_flow": scenario_params.get("capital_flow", 0.0),
            "initial_shock": scenario_params.get("initial_shock", 0.0)
        }

    def _asset_operators_step(self, scenario_params, macro_result, trade_result):
        """房地产+石油资产算子流"""
        house_price_change = scenario_params.get("house_price_change", 0.0)
        mortgage_rate_change = -macro_result["policy_intervention"] * 0.8
        equilibrium_house = 10000
        actual_house = equilibrium_house * (1 + house_price_change/100)
        house_deviation = (actual_house - equilibrium_house) / equilibrium_house
        sigma_house = np.clip(abs(house_deviation)*5 + macro_result["sigma"]*0.5, 0.05, 0.98)

        oil_price_change = scenario_params.get("oil_price_change", 0.0) - scenario_params.get("fed_rate_change", 0.0)*2
        oil_cpi_effect = oil_price_change * 0.02
        sigma_oil = np.clip(abs(oil_price_change/20) + trade_result["sigma_trade"]*0.7, 0.05, 0.98)

        print(f"\n🏠 【房地产算子流】")
        print(f"   Ξ 均衡房价锚定：{equilibrium_house}元/平")
        print(f"   Λ 房价偏离均衡：{house_deviation:+.1%}")
        print(f"   GTR 房贷利率变动：{mortgage_rate_change:+.2f}BP")
        print(f"   Σ 房地产不确定性：{sigma_house:.2f}")
        
        print(f"\n🛢️  【石油算子流】")
        print(f"   GTR 油价变动：{oil_price_change:+.1f}%，CPI传导效应{oil_cpi_effect:+.1%}")
        print(f"   Σ 石油不确定性：{sigma_oil:.2f}")

        return {
            "house_deviation": house_deviation,
            "mortgage_rate_change": mortgage_rate_change,
            "sigma_house": sigma_house,
            "oil_price_change": oil_price_change,
            "oil_cpi_effect": oil_cpi_effect,
            "sigma_oil": sigma_oil,
            "sigma_total": (sigma_house + sigma_oil) / 2
        }

    def _micro_operators_step(self, scenario_params, macro_result, trade_result, asset_result):
        """微观个人算子流（最终落地到钱包）"""
        monthly_income = scenario_params.get("monthly_income", 10000)
        debt_service = scenario_params.get("debt_service", 5000)
        job_security = scenario_params.get("job_security", 0.7)

        # 计算月供变化
        old_mortgage = debt_service * 0.8  # 假设80%是房贷
        new_mortgage = old_mortgage * (1 + asset_result["mortgage_rate_change"]/100)
        new_debt_service = debt_service - old_mortgage + new_mortgage
        
        # 计算早餐价格变化（生动案例）
        breakfast_old = 10
        breakfast_increase = (trade_result["cpi_effect"] + asset_result["oil_cpi_effect"])
        breakfast_new = breakfast_old * (1 + breakfast_increase)

        disposable_income = monthly_income - new_debt_service
        debt_ratio = new_debt_service / monthly_income
        sigma_personal = np.clip(
            (1-job_security)*0.4 + max(0, (debt_ratio-0.5))*0.3 +
            macro_result["sigma"]*0.3, 0.05, 0.98
        )

        print(f"\n👤 【微观个人算子流】（最终落地到你的钱包）")
        print(f"   Ξ 可支配收入：{disposable_income:.0f}元/月（月供变化：{new_mortgage-old_mortgage:+.0f}元）")
        print(f"   Λ 债务收入比：{debt_ratio:.0%}")
        print(f"   🍜 生动案例：早餐从{breakfast_old:.0f}元涨到{breakfast_new:.1f}元")
        print(f"   Σ 个人获得感不确定性：{sigma_personal:.2f}")

        if debt_ratio > 0.5 and sigma_personal > 0.5:
            print(f"   ℹ️  建议：减少可选消费，增加预防性储蓄")

        return {
            "disposable_income": disposable_income,
            "debt_ratio": debt_ratio,
            "breakfast_old": 10,
            "breakfast_new": breakfast_new,
            "breakfast_change": breakfast_new - 10,
            "sigma_personal": sigma_personal,
            "mortgage_change": new_mortgage - old_mortgage
        }

    def _auto_analysis(self):
        """自动输出伙伴们建议的完整结果分析"""
        res = self.full_result
        print("\n" + "=" * 80)
        print("📊 【天赐范式算子流推演结果深度分析】")
        print("-" * 80)

        # 1. 国际贸易分析
        trade_sigma = res["trade"]["sigma_trade"]
        print(f"📦 国际贸易算子流：{'高不确定性源头' if trade_sigma>0.7 else '中等不确定性' if trade_sigma>0.5 else '低不确定性'}")
        print(f"   Σ 贸易不确定性 = {trade_sigma:.2f} {'（接近极值，贸易端几乎完全不可预测）' if trade_sigma>0.9 else ''}")
        if abs(res["macro"]["rate_deviation"]) > 1:
            print(f"   τ {'强熔断已触发' if abs(res['macro']['rate_deviation'])>2 else '弱熔断已触发'}：政策利率偏离泰勒规则{res['macro']['rate_deviation']:.2f}%，模拟干预{res['macro']['policy_intervention']:.2f}%")

        # 2. 房地产分析
        house_sigma = res["asset"]["sigma_house"]
        house_dev = res["asset"]["house_deviation"]
        print(f"\n🏠 房地产算子流：{'中等不确定性' if house_sigma>0.5 else '低不确定性'}")
        print(f"   Λ 房价偏离均衡：{house_dev:+.1%}，{'未触发强预警' if abs(house_dev)<1 else '触发偏离预警'}")
        print(f"   GTR 房贷利率变动：{res['asset']['mortgage_rate_change']:+.2f}BP，月供变化{res['micro']['mortgage_change']:+.0f}元")
        print(f"   Σ 房地产不确定性 = {house_sigma:.2f}")

        # 3. 石油分析
        oil_sigma = res["asset"]["sigma_oil"]
        oil_change = res["asset"]["oil_price_change"]
        print(f"\n🛢️  石油算子流：{'高不确定性' if oil_sigma>0.7 else '中等不确定性' if oil_sigma>0.5 else '低不确定性'}")
        print(f"   GTR 油价变动：{oil_change:+.1f}%，CPI传导效应{res['asset']['oil_cpi_effect']:+.1%}")
        print(f"   Σ 石油不确定性 = {oil_sigma:.2f}")

        # 4. 微观个人分析
        personal_sigma = res["micro"]["sigma_personal"]
        print(f"\n👤 微观个人算子流：{'风险尚未完全暴露' if personal_sigma < res['global_sigma'] else '个人端已感知风险'}")
        print(f"   可支配收入：{res['micro']['disposable_income']:.0f}元/月，债务收入比{res['micro']['debt_ratio']:.0%}")
        print(f"   早餐价格从{res['micro']['breakfast_old']}元涨到{res['micro']['breakfast_new']:.1f}元，{'石油降价对冲了部分关税通胀' if res['asset']['oil_cpi_effect']<0 else ''}")
        print(f"   Σ 个人获得感不确定性 = {personal_sigma:.2f}")

        # 5. 全局全息分析
        global_sigma = res["global_sigma"]
        print(f"\n🌐 全系统全息耦合风险指数 = {global_sigma:.2f} {'（高风险）' if global_sigma>0.7 else '（中等风险）' if global_sigma>0.5 else '（低风险）'}")
        if personal_sigma < global_sigma:
            print(f"   核心预警：全局风险指数显著高于个人端不确定性，风险已经积累，但尚未完全传导到个人，存在明显时滞！")
        print(f"   核心能力：不是给出黑箱预测，而是白盒揭示风险的来源、传导路径和时滞效应")

        # 6. 建议
        print("\n💡 【算子流自动生成决策建议】")
        if abs(res["macro"]["policy_intervention"]) > 0:
            print(f"   政策层面：τ熔断已给出模拟干预路径，可参考{abs(res['macro']['policy_intervention']):.2f}%的利率反向调整")
        print(f"   个人层面：当前早餐仅涨{res['micro']['breakfast_change']:.1f}元，但贸易端不确定性{trade_sigma:.2f}，建议适当增加流动性储蓄，避免新增高杠杆负债")
        print(f"   企业/投资者：应关注外贸敞口和汇率风险，利用全息耦合指数作为压力测试依据")
        print("=" * 80)

# ====================== 可视化报告生成函数（对标AGI宝宝同款） ======================
def plot_economy_report(engine):
    """生成天赐范式全息经济学风险监测报告，6图联动，对标AGI宝宝视觉效果"""
    res = engine.full_result
    if not res:
        print("无推演数据，跳过报告生成")
        return

    # 提取数据
    sigma_data = {
        "宏观经济": res["macro"]["sigma"],
        "国际贸易": res["trade"]["sigma_trade"],
        "房地产": res["asset"]["sigma_house"],
        "石油市场": res["asset"]["sigma_oil"],
        "个人端": res["micro"]["sigma_personal"]
    }
    labels = list(sigma_data.keys())
    sigma_values = list(sigma_data.values())
    global_sigma = res["global_sigma"]
    mode_history = res["macro"]["history"]["mode"]
    step_history = res["macro"]["history"]["step"]
    sigma_history = res["macro"]["history"]["sigma_inflation"]

    # 创建画布，2行3列，和AGI宝宝报告布局一致
    fig = plt.figure(figsize=(15, 9))
    fig.suptitle("天赐范式·全息经济学风险监测报告", fontsize=16, fontweight="bold")

    # 子图1：各模块Σ不确定性对比
    ax1 = fig.add_subplot(2, 3, 1)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    bars = ax1.bar(labels, sigma_values, color=colors, alpha=0.7, edgecolor='black')
    ax1.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='高风险阈值')
    ax1.set_title("各模块Σ不确定性对比", fontsize=12)
    ax1.set_ylabel("Σ 不确定性（0~1）")
    ax1.set_ylim(0, 1)
    ax1.grid(axis='y', alpha=0.3)
    ax1.legend()
    # 给柱子加数值标签
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height+0.02, f'{height:.2f}', ha='center', va='bottom')

    # 子图2：风险模块占比饼图
    ax2 = fig.add_subplot(2, 3, 2)
    total_sigma = sum(sigma_values)
    sizes = [v/total_sigma for v in sigma_values]
    ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    ax2.set_title("各模块风险贡献占比", fontsize=12)

    # 子图3：算子风险雷达图
    ax3 = fig.add_subplot(2, 3, 3, projection='polar')
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    values = sigma_values + sigma_values[:1]
    angles += angles[:1]
    ax3.plot(angles, values, 'o-', linewidth=2, color='#d62728')
    ax3.fill(angles, values, alpha=0.25, color='#d62728')
    ax3.set_xticks(angles[:-1])
    ax3.set_xticklabels(labels)
    ax3.set_ylim(0, 1)
    ax3.set_title("风险雷达图", va='bottom', fontsize=12)

    # 子图4：通胀传导链路
    ax4 = fig.add_subplot(2, 3, 4)
    inflation_links = ["关税冲击", "进口价格", "国内CPI", "早餐价格"]
    inflation_values = [
        res["scenario"]["tariff_increase"]*100,
        res["trade"]["import_price_increase"]*100,
        res["trade"]["cpi_effect"]*100 + res["asset"]["oil_cpi_effect"]*100,
        res["micro"]["breakfast_change"]
    ]
    ax4.plot(inflation_links, inflation_values, 's-', linewidth=2, color='#ff7f0e')
    ax4.set_title("通胀传导链路", fontsize=12)
    ax4.set_ylabel("涨幅（%）")
    ax4.grid(axis='y', alpha=0.3)
    # 加数值标签
    for i, v in enumerate(inflation_values):
        ax4.text(i, v+0.1, f'{v:+.1f}%', ha='center', va='bottom')

    # 子图5：ZFC/¬CH模式切换历史
    ax5 = fig.add_subplot(2, 3, 5)
    ax5.plot(step_history, mode_history, 'g-', linewidth=1.5)
    ax5.set_yticks([0, 1])
    ax5.set_yticklabels(["ZFC均衡模式", "¬CH非均衡模式"])
    ax5.set_title("认知模式切换历史", fontsize=12)
    ax5.set_xlabel("推演步数")
    ax5.grid(axis='y', alpha=0.3)

    # 子图6：个人收支影响对比
    ax6 = fig.add_subplot(2, 3, 6)
    personal_items = ["月收入", "债务支出", "可支配收入"]
    personal_values_old = [
        res["scenario"]["monthly_income"],
        res["scenario"]["debt_service"],
        res["scenario"]["monthly_income"] - res["scenario"]["debt_service"]
    ]
    personal_values_new = [
        res["scenario"]["monthly_income"],
        res["scenario"]["debt_service"] + res["micro"]["mortgage_change"],
        res["micro"]["disposable_income"]
    ]
    x = np.arange(len(personal_items))
    width = 0.35
    ax6.bar(x - width/2, personal_values_old, width, label='推演前', color='#1f77b4', alpha=0.7)
    ax6.bar(x + width/2, personal_values_new, width, label='推演后', color='#d62728', alpha=0.7)
    ax6.set_title("个人收支影响对比", fontsize=12)
    ax6.set_xticks(x)
    ax6.set_xticklabels(personal_items)
    ax6.set_ylabel("金额（元）")
    ax6.legend()
    ax6.grid(axis='y', alpha=0.3)

    # 布局调整
    plt.tight_layout()
    # 保存图片
    plt.savefig("tianci_holo_economy_report.png", dpi=150, bbox_inches='tight')
    print("📊 全息经济学风险监测报告已保存为 tianci_holo_economy_report.png")
    # 显示图片
    plt.show()

# ====================== 主程序：场景测试 ======================
if __name__ == "__main__":
    print("🧠 天赐范式·全息经济学全系统引擎（可视化终极版）启动")
    print("=" * 80)
    
    # 定义测试场景：美联储加息50BP + 15%关税 + 房价下跌0.5%
    test_scenario = {
        "fed_rate_change": 0.5,          # 美联储加息50BP
        "tariff_increase": 0.15,         # 加征15%关税
        "house_price_change": -0.5,       # 房价下跌0.5%
        "actual_gdp_growth": 4.8,         # 实际GDP增长4.8%
        "inflation_rate": 1.8,            # 初始通胀1.8%
        "unemployment_rate": 5.3,          # 失业率5.3%
        "policy_rate": 2.0,                # 政策利率2.0%
        "consumption_growth": 5.5,         # 消费增长5.5%
        "investment_growth": 3.8,          # 投资增长3.8%
        "net_export_growth": 1.5,           # 净出口增长1.5%
        "forecast_variance": 1.5,          # 预测方差
        "survey_divergence": 30.0,         # 预期分歧
        "commodity_vol": 15.0,              # 大宗商品波动率
        "cny_usd_spread": -1.5,            # 中美利差-1.5%
        "geo_risk": 0.3,                    # 地缘风险
        "monthly_income": 10000,            # 月收入10000元
        "debt_service": 5200,               # 月债务支出5200元
        "job_security": 0.6,                # 就业稳定性0.6
        "import_share": 0.3                 # 进口消费占比30%
    }

    # 执行全链路推演
    engine = HolographicEconomyEngine()
    result = engine.step(test_scenario)
    
    # 自动生成可视化报告
    plot_economy_report(engine)
    
    print("\n✅ 推演与报告生成完成！算子即一切，一切即算子。")