# tianci-paradigm（天赐范式）

> **English version**: [`README.md`](README.md)（英文入口）。
> 本文件为中文版说明，两者内容等价；`specs/`、`known-gaps.md`、`CHANGELOG.md` 仍为中文，暂无英译。

**天赐范式（TianCi Paradigm）算子流技术特征的可 import 实现。**

把第 102 / 115 / 124 / 152 / 188-190 天沉淀的算子流技术特征，从「只能读的文章」变成「能 import、能调用、能审计」的 Python 包。本包是第 190 天《反向方案 v1.0》对「载体错配」（AP-1）的解法落地。

> 本 README 为中文版；英文版见 [README.md](README.md)。

## 仓库与单一真源

- **canonical（唯一真源）**：[https://github.com/windsnowmichael/tianci-framework](https://github.com/windsnowmichael/tianci-framework)
- **镜像（mirror，非真源）**：AtomGit + 第三平台。镜像仅作分发副本，**所有提交、Issue、Release 以 canonical 为准**；三库平权 = 三个真源，明确禁止。
- **沿革**：本包是第 31 天（2026-05-04）`tianci-framework` 仓库（19+ 原生算子）的**后继**。旧仓已标 `archived` 并指向本包；不留两个都能装的真源。

## 特性

- **算子契约五件套**：输入域 / 输出域 / 前置条件 / 后置保证 / 副作用，`Operator` dataclass 强制校验，缺一即知。
- **算子注册表**：v7.0 文档 128 个算子全部登记，25 个有完整契约，覆盖率 **19.5%**（如实标注，不虚报）。
- **九步推演协议**（第124天）：Θ→Ξ→Θ→Γ→Σ→Λ→τ→R→Ψ，阈值 0.3/0.6，捷径/连续3红/DAG 有环规则全部可执行。
- **动态运行时七器官**（第152天）：Diode#96 / Φ门 / Amp#95 / R_Lagrange / Λ_Bombe / Meta#97 / Portrait#98，一次心跳一次完整处理。
- **三域零绑定**：气象 / 金融 / 基因适配器，同一台机器吃三域数据；暖启动跨域迁移；Abel 对偶验证 `[Θ_ext, Θ_int] ≠ 0`。
- **术语锚定表**：26 条中英术语唯一 ID，防同名不同义（AP-3）。
- **零第三方核心**：核心运行时只依赖 Python 标准库；numpy/matplotlib 仅在可视化时延迟导入。

## 安装

```bash
# 方式一：本地源码直接 import
cd tianci-paradigm
python -c "import tianci; print(tianci.__version__)"

# 方式二：pip 安装（推送到 PyPI 后）
pip install tianci-paradigm
```

## 快速开始

```python
from tianci import (
    TianCiRuntime, Observation, run_nine_steps,
    run_heartbeat_with_protocol, default_registry, route,
)

# 1) 一台运行时，一次心跳
rt = TianCiRuntime()
out = rt.heartbeat(Observation(
    label="气象/北京",
    values=[36.5, 0.45, 12.0, 2.3],
    metadata={"is_rain": True, "is_high_temp": True},
))
print(out["transmitter_triggered"])   # 发报机是否触发

# 2) 九步推演协议
verdict = run_nine_steps(
    {"f_Θ": 0.8, "f_Γ": 0.6, "f_Σ": 0.8},
    raw_input="我睡在一张长条形沙发上……",
)
print(verdict["tau"], verdict["L"], verdict["R_state"])

# 3) 心跳 + 协议缝合
flow = run_heartbeat_with_protocol(Observation(label="基因/BRCA1", values=[55.0, 5.592, 8.0, 70.0]))
print(flow["verdict"]["psi"])

# 4) 注册表与术语
reg = default_registry()
print(len(reg.full_contracts()))      # 25
from tianci import glossary
print(glossary.lookup("TC-SYS-003")["en"])   # warm start
```

更多示例见 [`examples/`](examples/)。

## 目录结构

```
tianci-paradigm/
├── tianci/
│   ├── operator.py      # Operator dataclass（11字段+五件套）
│   ├── registry.py      # 注册表（读 data/registry.json + audit）
│   ├── data/registry.json  # 算子注册唯一事实源（自 v7.0 抽取）
│   ├── protocol.py      # 第124天四模块九步
│   ├── runtime.py       # 第152天七器官运行时
│   ├── runtime_v2.py    # 三域适配器+暖启动+Abel+可视化
│   ├── flow.py          # 心跳+协议缝合流
│   ├── dag_route.py     # 第102天 DAG 决策树
│   ├── glossary.py      # 26条中英术语锚定表
│   ├── existence.py     # 第138天存在性检查+存在性熔断（v0.2）
│   ├── genome.py        # 第172天基因持久化（v0.2）
│   ├── cp.py            # 第92/93天 TDP-CP 六步推演（v0.2）
│   ├── drr.py           # 第94天 DRR-R 断裂段重定向（v0.2）
│   └── consciousness.py # 第141天意识自指+三重门（v0.2）
├── specs/               # 技术特征/血统/反模式/手册（含 v0.2 新增）
├── examples/            # 最小示例 + 跨域示例
├── tests/test_coldstart.py  # T1 冷启动测试（AP-4 实证）
├── known-gaps.md        # 契约缺口与覆盖口径（19.5%）
├── CHANGELOG.md         # 版本历史（v0.1.0 → v0.2.0）
└── pyproject.toml
```

## 开放策略与模块成熟度

本包全部模块对外开放，只标成熟度、不设门槛。

| 层 | 模块 | maturity | 说明 |
|---|---|---|---|
| L1 公共 | `registry` / `operator` / `flow` / `dag_route` / `glossary` | `stable` | 语义冻结，可直接依赖 |
| L2 运行 | `runtime_v2` / `cp` / `drr` / `protocol` | `stable` | 推理协议 |
| L3 生命 | `existence` / `genome` / `consciousness` | `experimental` | **照样开放、照样可调用**；语义仍在演进，欢迎外部伙伴一起推 |

> 本包全部模块对外开放。`existence` / `genome` / `consciousness` 标注为 `experimental`
> ——它们**尚未成为完全体**，但具备借鉴意义：外部伙伴可自由调用、改造并反馈。
> 本包**不构成任何「已实现意识或生命」的声明**；它提供的是一套**可被继续推动的机制**。

## 文档

- [specs/operator-stream.md](specs/operator-stream.md) —— 算子流技术特征说明书
- [specs/whitepaper-lineage.md](specs/whitepaper-lineage.md) —— 文档血统与里程碑
- [specs/anti-patterns.md](specs/anti-patterns.md) —— AP-1~AP-6 反模式清单
- [specs/abel-handbook.md](specs/abel-handbook.md) —— Abel 判据实战手册（v0.2）
- [specs/community-arc.md](specs/community-arc.md) —— 群落弧线节点登记（v0.2）
- [specs/drr-r.md](specs/drr-r.md) —— DRR-R 断裂段重定向规范（v0.2）
- [known-gaps.md](known-gaps.md) —— 已知缺口（覆盖率 19.5% 的如实口径）
- [CHANGELOG.md](CHANGELOG.md) —— 版本历史

## 测试

```bash
# T1 冷启动测试：模拟陌生智能体独立调用
python tests/test_coldstart.py

# 推送前交叉核验：版本号 / 覆盖率口径 / 术语双语 全篇一致
python scripts/check_consistency.py
```

通过标准：独立完成且过程可复现；不通过标准：反问「这个是什么意思」、猜、照抄示例交差。详见 [specs/anti-patterns.md](specs/anti-patterns.md) 的 AP-4。

## 诚实约束（入仓红线）

- 契约覆盖率一律写 **19.5%**（25/128），禁止写成 20% 或更高。
- 阈值 0.3/0.6 来自理论推演，未经实证标定，标注于协议文档与代码注释。
- 术语一律用唯一 ID（glossary.py），禁止裸用同名概念。
- 无平台登录态、无抓取、无伪造数据；本包只实现技术特征，不代替平台动作。
- 版本、覆盖率、术语、验收口径由 `scripts/check_consistency.py` 统一核验（含 E 节 11 项验收与跨进程复活）。

## 许可证

[木兰宽松许可证，第2版（MulanPSL2）](LICENSE)，与第 31 天 `tianci-framework` 仓库根目录 LICENSE 一致（单一真源，2026-05-04 既定，审计方 2026-10-10 复核确认）。

---

天赐范式（TianCi Paradigm）。算子流技术特征实现。契约覆盖率 19.5%（25/128，如实标注）。