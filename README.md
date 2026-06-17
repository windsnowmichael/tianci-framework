# 天赐范式 · tianci-framework

[![CI](https://github.com/windsnowmichael/tianci-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/windsnowmichael/tianci-framework/actions/workflows/ci.yml)

**算子即一切，一切即算子。**

天赐范式是一套**白盒、可解释、可复现**的跨领域统一推演框架。以**公理化算子体系**为骨架，以**数学收敛性定理**为地基，以**可运行代码**为验证，覆盖计算流体力学、环境治理、全灾种应急、全息经济学等领域。

本仓库是天赐范式的完整代码实现，所有算子定义、数值求解器、验证脚本均对外公开。

---

## 核心贡献

1. **公理化算子框架**：5条公理 → 收敛定理 → 6个核心算子实例化 + 公理验证（论文 Section 3-4）
2. **NS方腔流推塔求解器**：涡量-流函数法，128→256→512三层网格外推，RK4时间积分，CG泊松求解
3. **自洽能量闭环**：PhaseLock定理保证算子调控不破坏系统能量单调性（论文 Section 5）
4. **跨领域Python引擎**：环境治理、全灾种应急、全息经济学——同一套算子体系，不同领域实例化

---

## 算子体系

天赐范式定义了**6个核心算子**（论文主体）+ 6个监察算子（附录A），均满足5条公理约束。

### 核心算子（PDE求解管道 + 自适应调控）

| 算子 | 符号 | 功能 | 公理验证 |
|------|------|------|----------|
| 梯度溯源 | Θ | 计算流场梯度，驱动自适应权重 | A1 A2 A3 A4 A5 |
| 自适应缩放 | Γ | tanh软饱和梯度自适应，γ̄为诊断指标 | A1 A2 A3 A4 A5 |
| 残差监控 | Σ | 泊松方程残差收敛度，0→1标准化 | A1 A2 A3 A4 A5 |
| 预警耦合 | Λ | 残差-缩放耦合预警，三级状态门控 | A1 A2 A3 A4 A5 |
| 状态门控 | Φ | {SAFE, WARNING, CRITICAL} 三态切换 | A1 A2 A3 A4 A5 |
| 回滚熔断 | τ | CRITICAL时触发状态回滚，有界回退步长 | A1 A2 A3 A4 A5 |

### 监察算子（附录A：有界性与单调性证明）

| 算子 | 功能 |
|------|------|
| M-Σ | 多源不确定性聚合，紧致上界 |
| ρ-弹性 | 预警弹性恢复，单调衰减 |
| Δ-饱和 | 算子饱和度检测，保证有界 |
| 一致性 | 算子间一致性校验 |
| Λ-耦合 | 跨算子耦合强度调节 |
| 曲率能量 | 梯度曲率能量估计 |

> 完整算子体系（67个算子、100+公式）见[算子与公式大全](天赐范式算子与公式大全.md)和[Day44双语版](TianCi_Paradigm_Day44_Operator_Compendium_CN_EN.md)。

---

## 论文投稿

本仓库包含面向不同期刊的独立投稿子仓库，各含完整源码、数据和验证脚本。

| 子仓库 | 目标期刊 | 核心内容 |
|--------|----------|----------|
| `TianciNS-JSC/` | J. Scientific Computing | 公理化算子框架 + 推塔收敛 + 消融实验 + Ghia验证 |
| `TianciNS-ComputersFluids/` | Computers & Fluids | 偏差公式 Deviation(Ny)=(Ny-2)/(Ny-1) + 三网格验证 |
| `TianciNS-JCP/` | J. Computational Physics | 完整NS求解器 + 算子流监控体系 |

---

## 仓库结构

```
tianci-framework/
├── TianciNS-JSC/              # JSC投稿：公理化算子框架论文
│   ├── src/                   #   C++求解器（推塔架构）
│   ├── data/                  #   数值实验数据
│   └── tests/                 #   验证脚本
├── TianciNS-ComputersFluids/  # Computers & Fluids投稿
│   ├── src/
│   ├── data/
│   └── tests/
├── TianciNS-JCP/              # JCP投稿
│   ├── src/
│   ├── data/
│   └── tests/
├── tianci_HJZL.py             # 环境治理引擎（CBAM碳边境、大气沉降→水质）
├── tianci_JZKZ.py             # 全灾种危情推演引擎（地震、洪水、复合巨灾）
├── tianci_HGJJ.py             # 全息经济学引擎（降权均衡、Φ约束）
├── guardian_*.py               # 守护者计划（算子集群联调）
├── mcp_server.py               # MCP算子流API服务
├── tianci_wormhole.py          # 天赐虫洞协议
├── tianci_blackbox.py          # 天赐黑盒
├── ks_solver.py                # Kuramoto-Sivashinsky求解器
├── ns_solver.py                # NS方程Python求解器
├── verify_medal.py             # 0.996确定性偏差验证
├── tianci_256/257/258.cpp      # 经典方腔流C++求解器（Ghia基准）
├── 天赐范式算子与公式大全.md    # 完整算子与公式文档
├── requirements.txt            # Python依赖
└── .github/workflows/          # CI/CD自动验收
```

---

## 快速开始

### 环境要求

- Python 3.8+（NumPy, Matplotlib, SciPy, Flask）
- C++17编译器（g++或MSVC，用于NS求解器）

### Python引擎

```bash
git clone https://github.com/windsnowmichael/tianci-framework.git
cd tianci-framework
pip install -r requirements.txt

# 环境治理引擎 — CBAM碳边境调节场景
python tianci_HJZL.py

# 全灾种危情推演 — 定日地震/华北洪水/复合巨灾
python tianci_JZKZ.py

# 全息经济学引擎
python tianci_HGJJ.py
```

### C++ NS求解器

```bash
# 编译（以JSC版为例）
cd TianciNS-JSC/src
g++ -O3 -std=c++17 -Wl,--stack,134217728 -o tower_v26.exe Tianci_NS80000.cpp

# 运行Re=100推塔
./tower_v26.exe --Re 100
```

---

## 确定性基准

256×256方腔流与Ghia et al. (1982)基准对比中，最大绝对误差恒定锁定在 **0.996078431372549 = 254/255**，十次以上独立运行精确到小数点后八位。此确定性偏差已用于：

- **天赐虫洞协议**：以0.996为密钥的混沌信道加密协议
- **天赐黑盒**：基于故障隔离的不可篡改数字存储

验证：`python verify_medal.py`

---

## 白盒承诺

天赐范式的核心承诺：**任何人都可以复现所有结果。**

- 所有核心算子均以 `def` 形式在代码中完整定义
- 每个引擎包含 `test_scenario` 字典，修改参数即可模拟不同场景
- 所有推演数据可追溯到明确的算子输入和计算公式
- C++求解器输出完整算子状态（Xi, Ph, Ga, Lm, tau, Cl），每步可审查

---

## 版权与引用

CC BY-SA 4.0 开源协议。学术研究、个人学习及非商业用途可自由使用；商业应用须另行获取授权。

建议引用格式：

> Huan Wang. (2026). tianci-framework: A white-box operator framework for cross-domain unified reasoning [Computer software]. GitHub. https://github.com/windsnowmichael/tianci-framework

---

## 关联仓库

| 平台 | 地址 |
|------|------|
| GitHub | https://github.com/windsnowmichael/tianci-framework |
| Gitee | https://gitee.com/windsnowmichael/tianci-framework |
| AtomGit | https://atomgit.com/gcw_lwUf3sWj/tianci-framework |

## 联系方式

- CSDN博客：https://blog.csdn.net/snowoftheworld
- 作者：汪涣（Huan Wang），独立研究者
