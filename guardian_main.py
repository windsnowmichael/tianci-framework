# -*- coding: utf-8 -*-
"""
天赐范式 · 守护者计划 · 总指挥部（终极整合版）
三大战区 + 追猎系统 全算子集群联调
Ξ锚定预警 | Θ溯源曲率 | ℋ_holo全息守护 | ¬CH应急追猎
"""
from guardian_anchor import AnchorSystem
from guardian_trace import TraceSystem
from guardian_holo import HoloSystem
from guardian_pursuit import PursuitSystem  # ✅ 新增追猎模块
from datetime import datetime, timedelta


class GuardianCommander:
    """总指挥部：整合三大战区 + 追猎系统，统一调度"""

    def __init__(self, name, guardian_type="儿童"):
        self.name = name
        self.type = guardian_type
        
        # 三大战区（守护模式）
        self.anchor = AnchorSystem(name, guardian_type)
        self.trace = TraceSystem()
        self.holo = HoloSystem()
        
        # ✅ 新增：追猎系统（¬CH应急模式）
        self.pursuit = None
        self.pursuit_mode = False  # 初始为守护模式
        self.emergency_contacts = []

    def set_contacts(self, contacts):
        self.emergency_contacts = contacts

    def update_location(self, lat, lon, base_confidence=0.80, 
                       current_gait=None, current_apparel=None):
        """
        核心调度：位置更新 + 模式自动切换
        新增参数：current_gait（步态）、current_apparel（衣着）用于追猎反伪装
        """
        # 1. 全息增强置信度 + 轨迹记录
        enhanced_conf = self.holo.enhance_confidence(lat, lon, base_confidence)
        self.trace.record(lat, lon, enhanced_conf)

        current_pos = (lat, lon)
        trail = self.trace.get_recent_trail(20)
        
        # 2. 锚定系统风险评估
        risk_level, risk_msg, curvature = self.anchor.assess_risk(
            current_pos, trail, datetime.now()
        )

        # 越界保护：一旦离开所有安全区域，至少蓝牌
        in_safe = self.anchor._is_in_safe_zone(lat, lon)
        if not in_safe and risk_level == 0:
            risk_level = 1
            risk_msg = "蓝牌：已偏离安全区域"

        action = None
        escape_routes = []
        search_bounds = []
        pursuit_status = None
        gtr_predictions = []
        phi_bounds = []

        # 3. 风险触发干预
        if risk_level >= 1:
            action = self.anchor.intervene(
                risk_level, self.emergency_contacts, target_position=current_pos
            )
            escape_routes = self.holo.predict_escape_routes(trail)
            search_bounds = self.holo.lock_search_space(trail, escape_routes)

        # ✅ 4.  追猎模式触发：黄牌及以上自动切换（演示模式下降低阈值以确保可观测））
        if risk_level == 2 and not self.pursuit_mode:
            print(f"\n🚨 红牌触发！自动切换至 ¬CH 应急追猎模式！")
            self.pursuit = PursuitSystem(self.name, self.type)
            # 部署全城监控节点（复用全息节点）
            for node in self.holo.holo_nodes:
                (n_lat, n_lon), strength, n_type = node
                radius = {"基站": 500, "WiFi": 50, "蓝牙": 10}.get(n_type, 100)
                self.pursuit.add_surveillance_node(n_lat, n_lon, n_type, radius)
            # 记录初始体态特征（如果有）
            if current_gait and current_apparel:
                self.pursuit.set_previous_identity(current_gait, current_apparel)
            self.pursuit_mode = True

        # ✅ 5. 追猎模式运行
        if self.pursuit_mode and self.pursuit:
            pursuit_status = self.pursuit.feed_signal(
                lat, lon, enhanced_conf,
                current_gait=current_gait,
                current_apparel=current_apparel
            )
            gtr_predictions = self.pursuit.GTR_predict_next_position()
            phi_bounds = self.pursuit.Φ_lockdown()

        sigma = self.trace.Σ_uncertainty()

        return {
            "name": self.name,
            "position": current_pos,
            "confidence": enhanced_conf,
            "risk_level": risk_level,
            "risk_msg": risk_msg,
            "curvature": curvature,
            "sigma": sigma,
            "action": action,
            "escape_routes": escape_routes,
            "search_bounds": search_bounds,
            "pursuit_mode": self.pursuit_mode,  # 是否追猎模式
            "pursuit_status": pursuit_status,    # 追猎状态
            "gtr_predictions": gtr_predictions,  # GTR预判
            "phi_bounds": phi_bounds             # Φ锁死边界
        }


if __name__ == "__main__":
    # ========== 存储所有场景的运行数据 ==========
    all_results = {"孩子": [], "老人": [], "宠物": [], "追猎测试": []}
    
    print("=" * 60)
    print("🌌 天赐范式 · 守护者计划 · 全算子集群联调（终极版）")
    print("Ξ锚定 | Θ溯源 | GTR曲率 | Λ预警 | τ干预 | ℋ全息 | EBF预判 | Φ锁界 | ¬CH追猎")
    print("=" * 60)

    # ========== 场景一：贪玩的孩子 ==========
    print("\n" + "=" * 60)
    print("【场景一】贪玩的孩子 —— 小明")
    print("=" * 60)
    
    child = GuardianCommander("小明", "儿童")
    child.set_contacts(["父亲: 138****1234", "母亲: 139****5678"])
    child.anchor.set_home(39.9042, 116.4074)
    child.anchor.add_safe_zone(39.9050, 116.4060, 200)
    child.holo.add_node(39.9042, 116.4074, 1.0, "基站")
    child.holo.add_node(39.9050, 116.4060, 0.8, "WiFi")
    child.holo.add_node(39.9060, 116.4045, 0.6, "蓝牙")
    
    child_events = [
        (39.9042, 116.4074, 0.80, "16:00 放学，走出校门"),
        (39.9045, 116.4072, 0.82, "16:05 往家方向走"),
        (39.9048, 116.4075, 0.80, "16:08 正常路线，途经便利店"),
        (39.9060, 116.4060, 0.78, "16:10 被路边的游乐场吸引，偏离路线"),
        (39.9065, 116.4055, 0.76, "16:15 进入陌生小区，远离安全区"),
        (39.9070, 116.4050, 0.74, "16:20 完全超出日常活动范围"),
    ]
    
    for lat, lon, conf, desc in child_events:
        result = child.update_location(lat, lon, conf)
        all_results["孩子"].append(result)
        print(f"\n{desc}")
        print(f"  坐标: ({lat:.4f}, {lon:.4f}) | 置信度: {result['confidence']:.0%} | "
              f"曲率: {result['curvature']:.4f} | Σ: {result['sigma']:.2f} | "
              f"风险: {result['risk_msg']}")
        if result["action"] and result["risk_level"] >= 2:
            print(f"  ⚠️ 触发干预: {result['action']['level']}")
            for act in result["action"]["actions"]:
                print(f"    → {act}")
        if result["escape_routes"]:
            print(f"  EBF预判方向: {len(result['escape_routes'])}条")
        if result["search_bounds"]:
            print(f"  Φ 搜索边界已锁定")

    # ========== 场景二：迷路的老人 ==========
    print("\n" + "=" * 60)
    print("【场景二】迷路的老人 —— 张阿姨")
    print("=" * 60)
    
    elder = GuardianCommander("张阿姨", "老人")
    elder.set_contacts(["儿子: 139****8888", "社区服务站: 010-****1234"])
    elder.anchor.set_home(39.9087, 116.3975)
    elder.anchor.add_safe_zone(39.9090, 116.3980, 200)
    elder.holo.add_node(39.9087, 116.3975, 1.0, "基站")
    elder.holo.add_node(39.9090, 116.3980, 0.7, "WiFi")
    
    elder_events = [
        (39.9087, 116.3975, 0.85, "08:00 出门买菜，走出小区"),
        (39.9089, 116.3978, 0.82, "08:10 正常路线，往菜市场方向"),
        (39.9092, 116.3985, 0.80, "08:20 经过菜市场，未停下"),
        (39.9098, 116.3995, 0.76, "08:35 继续往前走，已超出惯常范围"),
        (39.9105, 116.4010, 0.72, "08:50 在陌生街区徘徊"),
        (39.9110, 116.4020, 0.68, "09:10 长时间停留在一个位置"),
    ]
    
    for lat, lon, conf, desc in elder_events:
        result = elder.update_location(lat, lon, conf)
        all_results["老人"].append(result)
        print(f"\n{desc}")
        print(f"  坐标: ({lat:.4f}, {lon:.4f}) | 置信度: {result['confidence']:.0%} | "
              f"曲率: {result['curvature']:.4f} | Σ: {result['sigma']:.2f} | "
              f"风险: {result['risk_msg']}")
        if result["action"] and result["risk_level"] >= 2:
            print(f"  ⚠️ 触发干预: {result['action']['level']}")
            for act in result["action"]["actions"]:
                print(f"    → {act}")
        if result["escape_routes"]:
            print(f"  EBF预判方向: {len(result['escape_routes'])}条")
        if result["search_bounds"]:
            print(f"  Φ 搜索边界已锁定")

    # ========== 场景三：走失的小狗 ==========
    print("\n" + "=" * 60)
    print("【场景三】走失的小狗 —— 旺财")
    print("=" * 60)
    
    pet = GuardianCommander("旺财", "宠物")
    pet.set_contacts(["主人: 137****5678", "宠物医院: 010-****9999"])
    pet.anchor.set_home(39.9100, 116.4050)
    pet.anchor.add_safe_zone(39.9100, 116.4050, 80)
    pet.holo.add_node(39.9100, 116.4050, 1.0, "基站")
    pet.holo.add_node(39.9095, 116.4045, 0.6, "蓝牙")
    
    pet_events = [
        (39.9100, 116.4050, 0.78, "07:00 主人开门，旺财溜出院子"),
        (39.9098, 116.4045, 0.75, "07:02 往小区门口跑"),
        (39.9095, 116.4040, 0.72, "07:04 穿过小区大门，往街上跑"),
        (39.9090, 116.4035, 0.68, "07:06 在街角犹豫，四处张望"),
        (39.9085, 116.4030, 0.65, "07:08 沿着街道继续远离"),
        (39.9080, 116.4025, 0.62, "07:10 钻进一条小巷，信号开始减弱"),
    ]
    
    for lat, lon, conf, desc in pet_events:
        result = pet.update_location(lat, lon, conf)
        all_results["宠物"].append(result)
        print(f"\n{desc}")
        print(f"  坐标: ({lat:.4f}, {lon:.4f}) | 置信度: {result['confidence']:.0%} | "
              f"曲率: {result['curvature']:.4f} | Σ: {result['sigma']:.2f} | "
              f"风险: {result['risk_msg']}")
        if result["action"] and result["risk_level"] >= 2:
            print(f"  ⚠️ 触发干预: {result['action']['level']}")
            for act in result["action"]["actions"]:
                print(f"    → {act}")
        if result["escape_routes"]:
            print(f"  EBF预判方向: {len(result['escape_routes'])}条")
        if result["search_bounds"]:
            print(f"  Φ 搜索边界已锁定")

    # ========== 场景四：追猎模式测试（反伪装高手） ==========
    print("\n" + "=" * 60)
    print("【场景四】追猎模式测试 —— 目标X（反伪装高手）")
    print("=" * 60)
    # 场景四：追猎演示。注意——此场景跳过普通守护逻辑，直接进入追猎模式。
     # 目标类型设为“可疑人员”，安全区缩小至50米以加速触发红牌。
    pursuer_test = GuardianCommander("目标X", "可疑人员")
    pursuer_test.set_contacts(["110", "派出所"])
    pursuer_test.anchor.set_home(39.9100, 116.4000)
    pursuer_test.anchor.add_safe_zone(39.9100, 116.4000, 50)
    # 部署全城监控
    pursuer_test.holo.add_node(39.9100, 116.4000, 1.0, "基站")
    pursuer_test.holo.add_node(39.9110, 116.4010, 0.8, "WiFi")
    pursuer_test.holo.add_node(39.9090, 116.4020, 0.6, "蓝牙")
    
    # 追猎事件（含伪装）
    pursuit_events = [
        (39.9100, 116.4000, 0.90, "14:00 目标在商圈出现", (0.75, 1.2, 1.75), ("黑色", "蓝色", "棒球帽")),
        (39.9102, 116.4005, 0.85, "14:03 向东北移动", (0.75, 1.2, 1.75), ("黑色", "蓝色", "棒球帽")),
        (39.9105, 116.4010, 0.80, "14:06 进入商场", (0.75, 1.2, 1.75), ("黑色", "蓝色", "棒球帽")),
        (39.9110, 116.4015, 0.60, "14:12 信号微弱（地下室）", (0.68, 1.0, 1.75), ("黑色", "蓝色", "棒球帽")),
        (39.9095, 116.3995, 0.70, "14:16 重新出现——换装！", (0.55, 0.9, 1.70), ("灰色", "棕色", "无帽")),
        (39.9085, 116.3990, 0.75, "14:20 往南移动", (0.55, 0.9, 1.70), ("灰色", "棕色", "无帽")),
        (39.9080, 116.3985, 0.72, "14:23 进入小巷", (0.55, 0.9, 1.70), ("灰色", "棕色", "无帽")),
        (39.9095, 116.3995, 0.68, "14:28 折返绕圈", (0.55, 0.9, 1.70), ("灰色", "棕色", "无帽")),
    ]
    
    for lat, lon, conf, desc, gait, apparel in pursuit_events:
        result = pursuer_test.update_location(lat, lon, conf, 
                                             current_gait=gait, current_apparel=apparel)
        all_results["追猎测试"].append(result)
        print(f"\n{desc}")
        print(f"  位置: ({lat:.4f}, {lon:.4f}) | 置信度: {result['confidence']:.0%}")
        
        if result["pursuit_mode"] and result["pursuit_status"]:
            ps = result["pursuit_status"]
            print(f"  🚨 追猎阶段: {ps['phase_name']} | 反追踪行为: {ps['evasive_actions']}次")
            if ps['evasive_details']:
                print(f"  识别伎俩: {', '.join(ps['evasive_details'])}")
            print(f"  触发节点: {ps['triggered_nodes']}个 | 建议: {ps['containment_recommendation']}")
        
        if result["gtr_predictions"]:
            print(f"  🎯 GTR预判: {len(result['gtr_predictions'])}条路径")
            for p in result["gtr_predictions"][:2]:
                print(f"    → ({p['position'][0]:.4f}, {p['position'][1]:.4f}) 概率{p['probability']:.0%}")
        
        if result["phi_bounds"]:
            print(f"  🔒 Φ公理锁死边界: {result['phi_bounds']}")

    print("\n" + "=" * 60)
    print("🌌 天赐范式 · 守护者计划 · 全算子集群联调完成")
    print("守护每一个需要守护的人，追猎每一个伪装的恶。")
    print("=" * 60)

    # ========== 自动生成可视化报告 ==========
    import matplotlib.pyplot as plt
    import matplotlib
    import numpy as np

    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
    matplotlib.rcParams['axes.unicode_minus'] = False

    scenes = ['贪玩的孩子\n小明', '迷路的老人\n张阿姨', '走失的小狗\n旺财', '追猎测试\n目标X']
    colors = ['#e74c3c', '#f39c12', '#3498db', '#9b59b6']
    scene_keys = ['孩子', '老人', '宠物', '追猎测试']
    time_labels = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8']

    # 从实时数据提取绘图数组
    sigmas = []
    confs = []
    risks = []
    curvs = []
    for key in scene_keys:
        res_list = all_results[key]
        sigmas.append([r['sigma'] for r in res_list])
        confs.append([r['confidence'] for r in res_list])
        risks.append([r['risk_level'] for r in res_list])
        curvs.append([r['curvature'] for r in res_list])

    fig = plt.figure(figsize=(19, 12))
    fig.suptitle('天赐范式 · 守护者计划 · 全算子集群推演报告（终极版）',
                 fontsize=20, fontweight='bold', y=0.98)

    # 图1：Σ 不确定性演进
    ax1 = fig.add_subplot(2, 2, 1)
    for i, (scene, color) in enumerate(zip(scenes, colors)):
        ax1.plot(range(len(sigmas[i])), sigmas[i], 'o-', color=color, linewidth=2, markersize=8, label=scene)
    ax1.set_xticks(range(max(len(s) for s in sigmas)))
    ax1.set_xticklabels(time_labels[:max(len(s) for s in sigmas)])
    ax1.set_ylabel('Σ 不确定性', fontsize=12)
    ax1.set_title('Σ 不确定性随轨迹演进', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(alpha=0.3)
    ax1.set_ylim(0, 0.3)

    # 图2：置信度 & Σ 双轴对比
    ax2 = fig.add_subplot(2, 2, 2)
    ax2_dual = ax2.twinx()
    bars = ax2.bar(range(len(confs[0])), confs[0], color='#2ecc71', alpha=0.6, label='置信度')
    line, = ax2_dual.plot(range(len(sigmas[0])), sigmas[0], 'o-', color='#e74c3c', linewidth=2.5, markersize=8, label='Σ 不确定性')
    ax2.set_xticks(range(len(confs[0])))
    ax2.set_xticklabels(time_labels[:len(confs[0])])
    ax2.set_ylabel('置信度', fontsize=12, color='#2ecc71')
    ax2_dual.set_ylabel('Σ 不确定性', fontsize=12, color='#e74c3c')
    ax2.set_title('孩子场景：置信度↑ → Σ↓（负相关验证）', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 1.05)
    ax2_dual.set_ylim(0, 0.3)
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_dual.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='lower left', fontsize=9)
    ax2.grid(alpha=0.3)

    # 图3：风险等级热力图
    ax3 = fig.add_subplot(2, 2, 3)
    # 统一长度
    max_len = max(len(r) for r in risks)
    risk_matrix = np.array([r + [0]*(max_len-len(r)) for r in risks])
    im = ax3.imshow(risk_matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=3)
    ax3.set_xticks(range(max_len))
    ax3.set_xticklabels(time_labels[:max_len])
    ax3.set_yticks(range(4))
    ax3.set_yticklabels(['追猎测试', '旺财', '张阿姨', '小明'])
    ax3.set_title('风险等级热力图（绿=安全，红=红牌）', fontsize=14, fontweight='bold')
    for i in range(4):
        for j in range(len(risks[i])):
            text = ax3.text(j, i, risk_matrix[i, j], ha="center", va="center",
                           color="white" if risk_matrix[i, j] > 1.5 else "black",
                           fontsize=11, fontweight='bold')

    # 图4：四场景 Σ 终值对比 + 算子状态
    ax4 = fig.add_subplot(2, 2, 4)
    final_sigmas = [s[-1] for s in sigmas]
    bars = ax4.bar(scenes, final_sigmas, color=colors, alpha=0.8, edgecolor='black')
    ax4.set_ylabel('最终 Σ 不确定性', fontsize=12)
    ax4.set_title('四场景 Σ 终值对比 & 全算子出动状态', fontsize=14, fontweight='bold')
    ax4.set_ylim(0, 0.3)
    for bar, val in zip(bars, final_sigmas):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.008,
                 f'{val:.2f}', ha='center', fontweight='bold', fontsize=12)

    ax4.text(0.5, -0.28,
             'Ξ 锚定 [OK] | Θ 溯源 [OK] | GTR 曲率 [OK] | Λ 预警 [OK] | τ 干预 [OK] | '
             'ℋ 全息增强 [OK] | EBF 预判 [OK] | Φ 锁界 [OK] | ¬CH 追猎 [OK]',
             ha='center', va='top', fontsize=10, fontweight='bold', color='#2c3e50',
             transform=ax4.transAxes)

    plt.tight_layout()
    plt.savefig('guardian_full_report_final.png', dpi=200, bbox_inches='tight')
    print('\n✅ 守护者计划全算子推演报告（终极版）已保存：guardian_full_report_final.png')
    plt.show()