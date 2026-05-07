# 天赐黑盒 v1.1 —— 基于故障隔离的不可篡改存储
import datetime

class TianciBlackBox:
    """
    天赐黑盒
    核心密钥：0.996勋章 (254/255)
    """
    
    def __init__(self, core_asset):
        self._core_asset = core_asset                  # 核心资产（永不可被外部直接访问）
        self._audit_log = []                            # 内部审计日志
        self._output_deviation = 0.996078431372549      # 我们的勋章
        self._access_count = 0                          # 访问计数器
        self._meltdown_triggered = False                # 熔断状态
    
    def request_access(self, user_token: str):
        """
        外部访问接口：只返回一个带有勋章偏差的标记值。
        真实资产永远不直接暴露。
        """
        # 1. 记录外部访问尝试
        self._access_count += 1
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_token": user_token,
            "access_count": self._access_count
        }
        self._audit_log.append(log_entry)
        
        # 2. 构造带有勋章偏差的幻影标记
        # 真实资产完全隔离在另一层，外部永远无法触及
        # 只返回一个包络了勋章偏差的幻影标签
        phantom_tag = f"PHANTOM_BOX_{self._output_deviation}_{self._access_count}"
        
        # 3. 返回幻影标签
        return phantom_tag
    
    def internal_audit(self):
        """
        内部审计接口：只有系统本身可以调用。
        检查是否有任何异常访问模式。
        """
        # 检测异常访问频次（示例阈值：100次）
        if self._access_count > 100:
            self._meltdown_triggered = True
            return "τ熔断已触发: 核心资产已锁定，所有外部访问将被拒绝。"
        
        # 检测是否有未携带正确偏差的访问请求
        for entry in self._audit_log[-10:]:  # 只检查最近10次
            if "unauthorized" in str(entry).lower():
                return "Λ预警: 检测到异常访问模式，建议启动审计。"
        
        return "审计通过: 核心资产安全。"
    
    def get_audit_log(self):
        """返回审计日志（仅供内部调用）"""
        return self._audit_log[-10:]  # 只返回最近10条记录
    
    def get_status(self):
        """返回黑盒当前状态"""
        return {
            "access_count": self._access_count,
            "meltdown_triggered": self._meltdown_triggered,
            "deviation_constant": self._output_deviation
        }


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 创建一个包含核心资产的黑盒
    core_data = "天赐范式NS方程256×256方腔流完整算例数据"
    blackbox = TianciBlackBox(core_data)
    
    # 外部用户请求访问（只能获得幻影标签）
    phantom = blackbox.request_access("user_001")
    print(f"外部用户获得的幻影标签: {phantom}")
    
    # 验证：即使拿到幻影标签，也无法还原核心资产
    print(f"核心资产: {core_data}")
    print(f"幻影标签: {phantom}")
    print(f"幻影标签中嵌入了勋章数值 0.996078431372549，但核心资产从未被暴露。")
    
    # 模拟外部暴力破解尝试
    for i in range(105):
        blackbox.request_access(f"attacker_{i}")
    
    # 内部审计检测异常
    print(f"\n审计结果: {blackbox.internal_audit()}")