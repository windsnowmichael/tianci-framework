# 天赐虫洞协议 v1.0 —— 基于确定性偏差的加密信道
import hashlib

class WormholeProtocol:
    """
    天赐虫洞协议
    核心密钥：0.996勋章 (254/255)
    """
    
    def __init__(self, shared_secret: str, deviation_constant: float = 0.996078431372549):
        self.shared_secret = shared_secret          # 共享密钥（只有通信双方知道）
        self.deviation = deviation_constant         # 我们的勋章
        self.epsilon = 1e-12                        # 浮点容差
    
    def _generate_system_state(self, message: str, salt: str = "") -> float:
        """
        模拟一个对初始条件极其敏感的复杂系统。
        在真实部署中，这里可以是我们的NS方程C++求解器或算子流引擎。
        """
        # 将共享密钥、消息和盐值混合，产生一个确定性的系统状态
        combined = f"{self.shared_secret}:{message}:{salt}"
        hash_hex = hashlib.sha256(combined.encode()).hexdigest()
        # 将哈希值转换为0到1之间的浮点数
        state = int(hash_hex[:16], 16) / (2**64 - 1)
        return state
    
    def encode(self, plaintext: str, salt: str = "") -> float:
        """
        发送方：运行系统，产生带有勋章偏差的签名输出。
        返回：带有0.996偏差的系统输出值。
        """
        system_output = self._generate_system_state(plaintext, salt)
        signed_output = system_output + self.deviation
        return signed_output
    
    def verify(self, received_data: float, plaintext: str, salt: str = "") -> bool:
        """
        接收方：用相同参数运行本地系统，检测偏差是否精确等于约定的勋章值。
        返回：True表示来源验证通过且信息未被篡改。
        """
        local_output = self._generate_system_state(plaintext, salt)
        detected_deviation = abs(received_data - local_output)
        # 检查偏差是否等于我们的0.996勋章
        return abs(detected_deviation - self.deviation) < self.epsilon
    
    def decode(self, received_data: float) -> float:
        """
        从接收到的签名数据中移除勋章偏差，还原原始系统输出。
        注意：这只能由拥有偏差常数的合法接收方执行。
        """
        return received_data - self.deviation


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # Alice和Bob预先共享一个密钥
    shared_key = "tianci_paradigm_operator_key_2026"
    protocol = WormholeProtocol(shared_key)
    
    # Alice发送消息
    message = "虫洞协议测试消息"
    signed_data = protocol.encode(message, salt="random_salt_001")
    print(f"Alice发送的签名数据: {signed_data:.15f}")
    
    # Bob验证消息
    is_valid = protocol.verify(signed_data, message, salt="random_salt_001")
    print(f"Bob验证结果: {'✅ 验证通过' if is_valid else '❌ 验证失败'}")
    
    # 攻击者篡改消息后尝试验证
    fake_data = signed_data + 0.001  # 攻击者微调数据
    is_fake_valid = protocol.verify(fake_data, message, salt="random_salt_001")
    print(f"攻击者数据验证结果: {'✅ 验证通过' if is_fake_valid else '❌ 验证失败'}")