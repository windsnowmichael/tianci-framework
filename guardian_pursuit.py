# -*- coding: utf-8 -*-
"""
天赐范式 · 守护者计划 · 追踪模块 v2.0
升级：全算子集群进入 ¬CH 应急模式，识破伪装与改头换面。
"""
import math
import numpy as np
from datetime import datetime, timedelta

class PursuitSystem:
    """
    追猎系统：当普通预警升级为追猎行动时启用。
    目标特征：主动规避监控、信号断续、轨迹刻意绕圈、改换装扮。
    """
    def __init__(self, target_name, target_type="可疑人员"):
        self.name = target_name
        self.type = target_type
        self.mode = "¬CH"  # 直接进入应急模式
        
        # 目标最后已知状态
        self.last_known_position = None
        self.last_signal_time = None
        self.signal_gap_threshold = 120  # 信号中断超过120秒判定为主动关闭设备
        
        # 目标先前的体态特征（用于伪装识别）
        self.previous_gait = None  # (步幅, 步频, 身高)
        self.previous_apparel = None  # (上衣颜色, 下衣颜色, 帽子)
        
        # 反追踪行为特征库
        self.evasive_patterns = []
        
        # 全城监控节点（模拟摄像头、基站、WiFi探针）
        self.surveillance_nodes = []
        
        # 追猎阶段
        self.pursuit_phase = 1  # 1=追踪, 2=围堵, 3=收网
        self.containment_perimeter = []

    def add_surveillance_node(self, lat, lon, node_type, coverage_radius):
        """部署监控节点（摄像头、WiFi探针、基站）"""
        self.surveillance_nodes.append({
            "position": (lat, lon),
            "type": node_type,
            "radius": coverage_radius,
            "last_triggered": None
        })

    def set_previous_identity(self, gait, apparel):
        """记录目标的先前的体态与衣着"""
        self.previous_gait = gait
        self.previous_apparel = apparel

    def counter_disguise(self, current_gait, current_apparel):
        """ℋ_holo 反伪装算子：识别是否改头换面"""
        # 如果没有历史数据，无法对比
        if not self.previous_gait or not self.previous_apparel:
            return False
        
        # 对比体态特征（步幅变化超过20%视为异常）
        gait_changed = abs(current_gait[0] - self.previous_gait[0]) / self.previous_gait[0] > 0.2
        
        # 对比衣着特征（上衣和下衣同时改变视为伪装）
        apparel_changed = (current_apparel[0] != self.previous_apparel[0] and 
                          current_apparel[1] != self.previous_apparel[1])
        
        if gait_changed or apparel_changed:
            return True
        return False

    def feed_signal(self, lat, lon, confidence, timestamp=None, 
                    current_gait=None, current_apparel=None):
        """接收一次被动信号，支持伪装检测"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # 1. 检测伪装改扮
        if current_gait and current_apparel and self.previous_gait:
            if self.counter_disguise(current_gait, current_apparel):
                self.evasive_patterns.append({
                    "type": "改换装扮",
                    "timestamp": str(timestamp),
                    "analysis": "目标改变步态和衣着——这是专业反追踪行为，试图混入人群"
                })
                self.pursuit_phase = min(3, self.pursuit_phase + 1)
        
        # 2. 检测信号中断
        previous_position = self.last_known_position
        self.last_known_position = (lat, lon)
        
        if self.last_signal_time is not None:
            gap = (timestamp - self.last_signal_time).total_seconds()
            if gap > self.signal_gap_threshold:
                self.evasive_patterns.append({
                    "type": "信号中断",
                    "gap_seconds": gap,
                    "timestamp": str(timestamp),
                    "analysis": f"目标在 {gap:.0f} 秒内无任何信号，可能主动关闭设备或进入信号屏蔽区域"
                })
                self.pursuit_phase = min(3, self.pursuit_phase + 1)
        
        self.last_signal_time = timestamp
        
        # 3. 检测折返绕圈
        if len(self.evasive_patterns) >= 3:
            recent_positions = [self.last_known_position]
            if hasattr(self, '_recent_positions'):
                recent_positions = self._recent_positions + recent_positions
            self._recent_positions = recent_positions[-5:]
            
            if len(self._recent_positions) >= 4:
                start = self._recent_positions[0]
                end = self._recent_positions[-1]
                mid = self._recent_positions[len(self._recent_positions)//2]
                dist_start_end = self._haversine(start[0], start[1], end[0], end[1])
                dist_start_mid = self._haversine(start[0], start[1], mid[0], mid[1])
                if dist_start_end < 50 and dist_start_mid > 200:
                    self.evasive_patterns.append({
                        "type": "折返绕圈",
                        "timestamp": str(timestamp),
                        "analysis": "目标故意绕回原点，试图混淆追踪方向"
                    })
                    self.pursuit_phase = 3
        
        # 4. 更新监控节点状态
        for node in self.surveillance_nodes:
            dist = self._haversine(lat, lon, node["position"][0], node["position"][1])
            if dist < node["radius"]:
                node["last_triggered"] = str(timestamp)
        
        # 5. 更新目标的基准特征（确认其新身份）
        if current_gait:
            self.previous_gait = current_gait
        if current_apparel:
            self.previous_apparel = current_apparel
        
        return self.assess_pursuit_status()

    def _haversine(self, lat1, lon1, lat2, lon2):
        """球面距离（米）"""
        R = 6371000
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def assess_pursuit_status(self):
        """评估当前追猎状态"""
        return {
            "target": self.name,
            "mode": self.mode,
            "pursuit_phase": self.pursuit_phase,
            "phase_name": {1: "追踪中", 2: "围堵中", 3: "收网中"}[self.pursuit_phase],
            "last_position": self.last_known_position,
            "evasive_actions": len(self.evasive_patterns),
            "evasive_details": [e["type"] for e in self.evasive_patterns],
            "signal_gap_seconds": (
                (datetime.now() - self.last_signal_time).total_seconds()
                if self.last_signal_time else 0
            ),
            "triggered_nodes": sum(1 for n in self.surveillance_nodes if n["last_triggered"]),
            "containment_recommendation": (
                "扩大搜索范围，通知所有监控节点" if self.pursuit_phase == 1
                else "封锁周边出口，部署人员值守" if self.pursuit_phase == 2
                else "收网：目标已锁定，立即行动"
            )
        }

    def GTR_predict_next_position(self):
        """
        GTR 曲率预测：基于已知轨迹和反追踪模式，预测目标下一步可能出现的位置。
        """
        if not self.last_known_position:
            return []
        
        lat, lon = self.last_known_position
        predictions = []
        
        if any(e["type"] == "折返绕圈" for e in self.evasive_patterns):
            predictions.append({
                "position": (lat + 0.001, lon - 0.001),
                "probability": 0.4,
                "reason": "绕圈模式：可能返回之前经过的节点"
            })
        
        if any(e["type"] == "信号中断" for e in self.evasive_patterns):
            predictions.append({
                "position": (lat + 0.002, lon + 0.001),
                "probability": 0.35,
                "reason": "信号恢复：可能从屏蔽区边缘重新出现"
            })
        
        if any(e["type"] == "改换装扮" for e in self.evasive_patterns):
            predictions.append({
                "position": (lat - 0.001, lon + 0.002),
                "probability": 0.30,
                "reason": "伪装后：可能混入人群，向人流密集区移动"
            })
        
        if self.surveillance_nodes:
            nearest = min(self.surveillance_nodes, 
                         key=lambda n: self._haversine(lat, lon, n["position"][0], n["position"][1]))
            away_lat = lat + (lat - nearest["position"][0]) * 0.5
            away_lon = lon + (lon - nearest["position"][1]) * 0.5
            predictions.append({
                "position": (away_lat, away_lon),
                "probability": 0.25,
                "reason": "远离最近监控节点"
            })
        
        return sorted(predictions, key=lambda p: p["probability"], reverse=True)

    def Φ_lockdown(self):
        """Φ 公理门控：锁死追猎计算空间"""
        if not self.last_known_position or self.pursuit_phase < 3:
            return []
        
        lat, lon = self.last_known_position
        margin = 0.005
        return [
            (lat - margin, lon - margin),
            (lat + margin, lon + margin)
        ]


# ==================== 追猎模式测试 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("天赐范式 · 守护者计划 · 追猎模式 v2.0")
    print("全算子进入 ¬CH 应急状态 · 反伪装模块已启用")
    print("=" * 60)
    
    pursuer = PursuitSystem("目标X", "可疑人员")
    
    # 部署全城监控节点
    pursuer.add_surveillance_node(39.9100, 116.4000, "摄像头", 100)
    pursuer.add_surveillance_node(39.9110, 116.4010, "WiFi探针", 50)
    pursuer.add_surveillance_node(39.9090, 116.4020, "基站", 500)
    pursuer.add_surveillance_node(39.9080, 116.3990, "摄像头", 100)
    
    # 记录目标的原始特征
    pursuer.set_previous_identity((0.75, 1.2, 1.75), ("黑色", "蓝色", "棒球帽"))
    
    print("\n【追猎场景：反追踪高手】")
    print("-" * 60)
    
    events = [
        # (lat, lon, conf, desc, gait, apparel)
        (39.9100, 116.4000, 0.90, "14:00 目标在商圈出现", 
         (0.75, 1.2, 1.75), ("黑色", "蓝色", "棒球帽")),
        (39.9102, 116.4005, 0.85, "14:03 向东北移动，WiFi探针嗅探到设备",
         (0.75, 1.2, 1.75), ("黑色", "蓝色", "棒球帽")),
        (39.9105, 116.4010, 0.80, "14:06 进入商场",
         (0.75, 1.2, 1.75), ("黑色", "蓝色", "棒球帽")),
        (39.9110, 116.4015, 0.60, "14:12 信号微弱，可能进入地下室",
         (0.68, 1.0, 1.75), ("黑色", "蓝色", "棒球帽")),
        # 换装后重新出现
        (39.9095, 116.3995, 0.70, "14:16 重新出现——但步态和衣着已完全不同！",
         (0.55, 0.9, 1.70), ("灰色", "棕色", "无帽")),
        (39.9085, 116.3990, 0.75, "14:20 往南移动，试图混入人群",
         (0.55, 0.9, 1.70), ("灰色", "棕色", "无帽")),
        (39.9080, 116.3985, 0.72, "14:23 进入小巷，信号再次减弱",
         (0.55, 0.9, 1.70), ("灰色", "棕色", "无帽")),
        (39.9095, 116.3995, 0.68, "14:28 绕回之前的点位——折返绕圈",
         (0.55, 0.9, 1.70), ("灰色", "棕色", "无帽")),
    ]
    
    for lat, lon, conf, desc, gait, apparel in events:
        status = pursuer.feed_signal(lat, lon, conf, 
                                     current_gait=gait, current_apparel=apparel)
        print(f"\n{desc}")
        print(f"  位置: ({lat:.4f}, {lon:.4f}) | 置信度: {conf:.0%}")
        print(f"  追猎阶段: {status['phase_name']} | 反追踪行为: {status['evasive_actions']}次")
        if status['evasive_details']:
            print(f"  识别到的反追踪伎俩: {', '.join(status['evasive_details'])}")
        print(f"  已触发监控节点: {status['triggered_nodes']}个")
        print(f"  建议: {status['containment_recommendation']}")
    
    predictions = pursuer.GTR_predict_next_position()
    if predictions:
        print(f"\n🎯 GTR 预判下一步位置:")
        for p in predictions:
            print(f"  → ({p['position'][0]:.4f}, {p['position'][1]:.4f}) "
                  f"概率: {p['probability']:.0%} | {p['reason']}")
    
    bounds = pursuer.Φ_lockdown()
    if bounds:
        print(f"\nΦ 公理锁死收网边界:")
        print(f"  左下: ({bounds[0][0]:.4f}, {bounds[0][1]:.4f})")
        print(f"  右上: ({bounds[1][0]:.4f}, {bounds[1][1]:.4f})")
    
    print("\n" + "=" * 60)
    print("追猎模式 v2.0 测试完成。")
    print("就算改头换面，也逃不出算子的罗网。")
    print("=" * 60)