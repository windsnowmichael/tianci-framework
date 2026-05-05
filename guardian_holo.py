# -*- coding: utf-8 -*-
"""
天赐范式 · 守护者计划 第三战区
ℋ_holo 全息节点 | EBF 蝴蝶推演 | Φ 公理门控
负责：全城节点联动、逃逸路径预测、搜索空间锁定
"""
import math
import numpy as np

class HoloSystem:
    def __init__(self):
        self.holo_nodes = []      # 标准格式：[(坐标, 信号强度, 节点类型), ...]
        self.escape_predictions = []  # EBF逃逸预判结果

    def add_node(self, lat, lon, strength, node_type):
        """
        部署ℋ_holo全息辅助节点（基站/WiFi/蓝牙）
        """
        strength = max(0.0, min(1.0, strength))
        self.holo_nodes.append(((lat, lon), strength, node_type))

    def enhance_confidence(self, lat, lon, base_confidence):
        """
        ℋ_holo 核心：全城节点交叉验证，增强定位置信度
        输入：目标坐标、基础置信度
        输出：增强后置信度 0~0.99
        """
        if not self.holo_nodes:
            return round(base_confidence, 4)

        total_boost = 0.0
        # 不同节点覆盖半径
        coverage_map = {"基站": 500, "WiFi": 50, "蓝牙": 10, "默认": 100}
        
        for (node_lat, node_lon), strength, node_type in self.holo_nodes:
            dist = math.hypot(lat - node_lat, lon - node_lon)
            coverage = coverage_map.get(node_type, 100)
            
            if dist < coverage:
                # 距离越近、信号越强，增益越大
                boost = strength * (1 - dist / coverage)
                total_boost += boost

        # 增益上限 0.2，总置信度上限 0.99
        enhanced = min(0.99, base_confidence + min(total_boost, 0.20))
        return round(enhanced, 4)

    def predict_escape_routes(self, trail, num_predictions=3):
        """
        EBF 蝴蝶效应：基于历史轨迹推演逃逸路径
        输入：轨迹列表、预判数量
        输出：[(路径坐标列表, 概率), ...]
        """
        self.escape_predictions = []
        if len(trail) < 5:
            return self.escape_predictions

        # 提取最近5个坐标
        recent = [p[1] for p in trail[-5:]]
        dx = recent[-1][0] - recent[0][0]
        dy = recent[-1][1] - recent[0][1]
        speed = math.hypot(dx, dy)

        if speed < 0.0001:
            return self.escape_predictions

        main_dir = (dx, dy)
        current_pos = recent[-1]

        # 主方向（50%）
        self.escape_predictions.append((
            [(current_pos[0]+main_dir[0]*2, current_pos[1]+main_dir[1]*2)], 0.5
        ))
        # 左偏30°（25%）
        angle = math.radians(30)
        lx = main_dir[0]*math.cos(angle) - main_dir[1]*math.sin(angle)
        ly = main_dir[0]*math.sin(angle) + main_dir[1]*math.cos(angle)
        self.escape_predictions.append((
            [(current_pos[0]+lx*1.5, current_pos[1]+ly*1.5)], 0.25
        ))
        # 右偏30°（25%）
        angle = math.radians(-30)
        rx = main_dir[0]*math.cos(angle) - main_dir[1]*math.sin(angle)
        ry = main_dir[0]*math.sin(angle) + main_dir[1]*math.cos(angle)
        self.escape_predictions.append((
            [(current_pos[0]+rx*1.5, current_pos[1]+ry*1.5)], 0.25
        ))

        return self.escape_predictions[:num_predictions]

    def lock_search_space(self, trail, predicted_routes):
        """
        Φ 公理门控：锁定追踪搜索空间，防止目标脱离监控
        输入：轨迹、预判路径
        输出：搜索边界 [(min_lat, max_lat), (min_lon, max_lon)]
        """
        if not trail or (not predicted_routes and len(trail) < 3):
            return [(0.0, 0.0), (0.0, 0.0)]

        # 收集所有坐标
        all_points = [p[1] for p in trail]
        for route, _ in predicted_routes:
            all_points.extend(route)

        lats = [p[0] for p in all_points]
        lons = [p[1] for p in all_points]

        # 扩展边界 500米（经纬度偏移）
        margin = 0.005
        min_lat = round(min(lats) - margin, 4)
        max_lat = round(max(lats) + margin, 4)
        min_lon = round(min(lons) - margin, 4)
        max_lon = round(max(lons) + margin, 4)

        return [(min_lat, max_lat), (min_lon, max_lon)]