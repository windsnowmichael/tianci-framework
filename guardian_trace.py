# -*- coding: utf-8 -*-
"""
天赐范式 · 守护者计划 第二战区
Θ 溯源系统 | GTR 轨迹曲率 | Σ 不确定性
负责：轨迹记录、偏离度计算、置信度统计、历史溯源
✅ 已修复：高置信度下Σ值异常问题
"""
import numpy as np
import math
from datetime import datetime

class TraceSystem:
    def __init__(self):
        self.trail = []           # 标准格式：[(timestamp, (lat,lon), confidence), ...]
        self.max_length = 10000  # 最大轨迹存储长度

    def record(self, lat, lon, confidence):
        """
        Θ 溯源：记录定位轨迹
        输入：经纬度、基础置信度
        输出：无
        """
        now = datetime.now()
        # 裁剪超长轨迹
        if len(self.trail) >= self.max_length:
            self.trail = self.trail[1:]
        self.trail.append((now, (lat, lon), round(confidence, 4)))

    def compute_deviation(self, safe_zones, routine_schedule, timestamp=None):
        """
        GTR 轨迹曲率 + 安全偏离度计算
        输入：安全区域列表、惯常时刻表、当前时间
        输出：(总偏离度 0~1, 轨迹曲率 弧度)
        """
        # 1. 计算轨迹曲率（GTR核心）
        curvature = 0.0
        if len(self.trail) >= 3:
            recent = [p[1] for p in self.trail[-5:]]
            angles = []
            for i in range(1, len(recent) - 1):
                dx1 = recent[i][0] - recent[i-1][0]
                dy1 = recent[i][1] - recent[i-1][1]
                dx2 = recent[i+1][0] - recent[i][0]
                dy2 = recent[i+1][1] - recent[i][1]
                
                norm1 = math.hypot(dx1, dy1)
                norm2 = math.hypot(dx2, dy2)
                if norm1 == 0 or norm2 == 0:
                    continue
                
                dot = dx1*dx2 + dy1*dy2
                cos_angle = max(-1, min(1, dot / (norm1 * norm2)))
                angles.append(math.acos(cos_angle))
            curvature = round(np.mean(angles) if angles else 0.0, 4)

        # 2. 计算安全区域偏离度
        dev_safe = 1.0
        if self.trail:
            current = self.trail[-1][1]
            for (center, radius) in safe_zones:
                dist = math.hypot(current[0]-center[0], current[1]-center[1])
                if dist < radius:
                    dev_safe = dist / radius
                    break

        # 3. 总偏离度（归一化 0~1）
        total_deviation = round(min(1.0, (dev_safe + curvature / 3.14) / 2), 4)
        return total_deviation, curvature

    def get_recent_trail(self, num_points=10):
        """
        返回最近N条轨迹数据（溯源用）
        """
        return self.trail[-num_points:]

    def get_confidence_stats(self):
        """
        轨迹置信度统计：均值、最低值、趋势
        输出：(均值, 最低值, 趋势: up/down/steady)
        """
        if not self.trail:
            return 0.0, 0.0, "steady"
        
        conf_list = [p[2] for p in self.trail]
        avg_conf = round(np.mean(conf_list), 2)
        min_conf = round(min(conf_list), 2)
        
        # 置信度趋势判断
        recent = conf_list[-5:]
        if len(recent) >= 2:
            trend = "up" if np.mean(recent[-3:]) > np.mean(recent[:3]) else "down"
        else:
            trend = "steady"
        
        return avg_conf, min_conf, trend

    def Σ_uncertainty(self):
        """
        ✅ 修复完成：Σ 不确定性算子
        逻辑：置信度越高 → 不确定性越低
        轨迹不足3点时，仅添加轻微惩罚，不再硬编码0.90
        输出：0~1，数值越高表示定位越不可靠。
        """
        # 完全无轨迹数据：最高不确定性
        if len(self.trail) == 0:
            return 0.95
        
        avg_conf, _, _ = self.get_confidence_stats()
        
        # 动态轨迹惩罚：轨迹越短，轻微加罚；轨迹越长，惩罚归零
        if len(self.trail) < 3:
            trail_penalty = 0.15
        else:
            trail_penalty = max(0, 0.05 - len(self.trail) * 0.0005)
        
        # 核心公式：不确定性 = 1 - 置信度 + 动态惩罚
        uncertainty = round(1.0 - avg_conf + trail_penalty, 2)
        return max(0.05, min(0.95, uncertainty))