# 天赐范式：算子流技术特征（Operator Stream）

> 本文件是 `tianci-paradigm` 包的技术特征说明书——回答「这套东西的算子流到底是什么、怎么用、边界在哪」。
> 与第124天《技术协议 v0.1》(四模块)、第102天《最小化技术特征 v1.0》(Operator dataclass)、第152天《动态运行时》(七器官) 同源，代码见 `tianci/`。

---

## 1. 一句话定位

天赐范式算子流 = 一组**带接口契约的算子**（输入域 / 输出域 / 前置条件 / 后置保证）+ 一条**九步推演协议**（感知→锚定→度量→量化→预警→判定→状态→自指）+ 一台**动态运行时**（七器官，把推演跑成可观测、可审计、可迁移的状态机）。

算子流的核心不是算子多，而是**三层分离**：

```
┌─────────────────────────────────────────────────────────┐
│  数据获取层（media-data）   —— 只取数，不做判断           │
├─────────────────────────────────────────────────────────┤
│  算子契约层（tianci.operator / registry）                │
│    128 个算子被登记在册，25 个有完整五件套契约，19.5%     │
├─────────────────────────────────────────────────────────┤
│  推演协议层（tianci.protocol）  —— 九步标准调用流程       │
│  Θ→Ξ→Θ→Γ→Σ→Λ→τ→R→Ψ                                    │
├─────────────────────────────────────────────────────────┤
│  运行时层（tianci.runtime / runtime_v2）                 │
│    七器官把观测变成心跳，把心跳变成画像                   │
├─────────────────────────────────────────────────────────┤
│  缝合流（tianci.flow）        —— 运行时证据 → 协议裁定    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 算子契约：五件套

一个「全契约算子」必须回答五个问题（第102天 Operator dataclass 的 11 字段压缩为五件套必填，其余为元信息）：

| 具 | 字段（英文） | 对应中文键 | 回答的问题 |
|---|---|---|---|
| 输入域 | `input_domain` | 输入域 | 算子吃什么样的数据（类型+范围） |
| 输出域 | `output_domain` | 输出域 | 算子吐什么样的结果 |
| 前置条件 | `preconditions` | 前置条件 | 什么状态下才允许调用 |
| 后置保证 | `post_guarantees` | 后置保证 | 调用成功后承诺什么 |
| 副作用 | `side_effects` | 副作用 | 调用会改变什么外部状态 |

```python
from tianci import Operator

op = Operator.from_spec({
    "名称": "Ψ_predict 自指预测",
    "输入域": "状态向量 S ∈ R^n，n≤10",
    "输出域": "预测分布 p(S_{t+1}) ∈ [0,1]^k",
    "前置条件": "Γ 度量已完成，D 非空",
    "后置保证": "输出自指描述且锚定 Γ 基准",
    "副作用": "写入 Portrait#98",
})
assert op.has_full_contract()   # True => 五件套齐全
```

- 五件套由 `operator.py` 的 `CORE_CONTRACT_FIELDS` 定义：`input_domain / output_domain / preconditions / post_guarantees / side_effects`。
- 额外存档字段：`name / version / contract_level / registry_num / source_line / name_cn`——它们是**溯源**，不是契约的一部分。
- `from_spec` 宽松键映射：接受中文键（输入域/输出域/前置条件/后置保证/副作用）或英文键，缺键即缺失字段。

---

## 3. 注册表：128 声明 / 25 契约 / 19.5% 覆盖率

`registry.json` 是唯一事实源（从 v7.0 文档自动抽取，脚本 `scripts/build_registry.py`）：

| 区间 | 内容 | 数量 | 契约状态 |
|---|---|---|---|
| `#1 – #25` | 算子流核心 | 25 | **全契约（五件套齐全）** |
| `#100 – #128` | 领域专属算子（气象/金融/基因等） | 29 | 半契约（仅名称/说明，缺五件套） |
| `#68 – #91` | 补齐+跨域算子 | 26 | 半契约 |
| 核心9 + 物理15 + 进化3 | R 算子（动态平衡） | 27 | 半契约 |
| 其余 | 索引有、未抽取 | ~21 | 无契约（仅索引条目） |
| **合计** | v7.0 文档声明 | **128** | **契约覆盖率 = 25/128 = 19.5%** |

```python
from tianci import default_registry

reg = default_registry()
reg.meta          # {'declared_total': 128, 'contracts_total': 25, 'coverage_pct': 19.5, ...}
reg.full_contracts()   # 25 个五件套齐全的算子
reg.get("Ψ_predict")   # 按名称查
reg.get_by_num(1)      # 按 #编号 查
reg.audit()            # 一致性审计：meta 与数据是否自洽
```

**诚实性约束（红线）**：覆盖率 19.5% 是抽取器实际结果。任何材料（README / known-gaps / 推送文案）不得虚报为 20% 或更高。缺契约的 103 个算子的定义缺口写在 `known-gaps.md`，不掩盖。

---

## 4. 推演协议：九步标准流程（第124天《技术协议 v0.1》）

| 步 | 符号 | 名称 | 动作 | 判定 |
|---|---|---|---|---|
| 1 | Θ | 输入接收标准化 | 分类输入，映射算子语义域 | 失败→触发Λ→τ=rollback |
| 2 | Ξ | 目标锚定 | 输入翻译为框架目标问题集合 G | — |
| 3 | Θ | 感知读入 | 提取特征向量 F | F方差≈0→调试模式 |
| 4 | Γ | 度量 | 特征与基准的偏差向量 D | 全部 d_i<0.1→**捷径跳第9步 pass**；任一 d_i>0.7→Λ严重预警 |
| 5 | Σ | 不确定性量化 | Σ_total = (Σd_i²)^(1/2)/√n ∈ [0,1] | — |
| 6 | Λ | 预警 | <0.3 绿 / 0.3-0.6 黄 / ≥0.6 红 | 连续3次红→强制 fail |
| 7 | τ | 判定 | pass / rollback / fail | DAG 有环→强制 fail |
| 8 | R | 状态机 | PASSIVE / ACTIVE / EMERGENCY | — |
| 9 | Ψ | 自指输出 | {τ, L, R_state, Ψ描述, 日志} | — |

```python
from tianci import run_nine_steps

result = run_nine_steps(
    {"f_Θ": 0.8, "f_Γ": 0.6, "f_Σ": 0.8},   # 特征向量
    raw_input="我睡在一张长条形沙发上……",     # 原文（第1步标准化）
)
result["tau"]   # 'fail' / 'rollback' / 'pass'
result["L"]     # '红色' / '黄色' / '绿色'
result["psi"]   # Ψ 自指输出
```

阈值说明（如实）：0.3 / 0.6 来自理论推演，**未经实证标定**，v0.2 可能调整。代码里 `THRESHOLD_YELLOW / THRESHOLD_RED / SHORTCUT_DEVIATION / SEVERE_DEVIATION` 均可改。

---

## 5. 动态运行时：七器官（第152天）

一次心跳 = 一次对观测的完整处理，七器官依次介入：

| # | 器官 | 英文/编号 | 职能 |
|---|---|---|---|
| ① | 半导体单向导通 | Diode#96 | 格式净化：拦空标签/空向量/NaN/Inf，不做价值判断 |
| ② | 逻辑门阵列 | Φ 门控 | 自动从 metadata 布尔字段做 AND/OR/NOT/XOR |
| ③ | 放大电路 | Amp#95 | Γ(t)=Θ(t)+α·Γ(t-Δt)，超阈值截断锁定 |
| ④ | 拉格朗日点突触 | R_Lagrange | 动态平衡点：偏离超半径自动调频迁移 |
| ⑤ | 发报机模式 | Λ_Bombe | 六维监察 ρ/σ/δ/λ/C²/MΣ 任一越界即发报 |
| ⑥ | 元系统引擎 | Meta#97 | 发报后回溯画像、生成补丁；V2 起补丁真正回填参数 |
| ⑦ | 意识动力学画像 | Portrait#98 | 全轨迹存档，可审计、可迁移 |

```python
from tianci import TianCiRuntime, Observation

rt = TianCiRuntime()
out = rt.heartbeat(Observation(label="气象/北京", values=[36.5, 0.45, 12.0, 2.3]))
out["transmitter_triggered"]     # 发报机是否触发
rt.export_portrait()             # 完整画像
rt.self_status()                 # 自指节点：本文陈述自身状态
```

**零绑定**：Observaton 不绑定任何业务字段；Weather/Finance/Gene 三个适配器把业务数据翻译成通用向量，同一台机器可吃三域数据（`runtime_v2.run_cross_domain()` 实证）。

**暖启动**：画像蒸馏为 `WarmStartPack`（平衡点/放大尾迹/突触尾迹/参数），注入新机器即可跨域迁移记忆（`migrate_and_run`）。

**Abel 对偶验证**：`abel_duality_test` 证明 `[Θ_ext, Θ_int] ≠ 0` —— 先外后内与先内后外的终态不同，交换子范数非零。

---

## 6. 缝合流：运行时证据 → 协议裁定

`tianci.flow` 把两步缝成一条主链路：**心跳产生六维监察证据 → 证据作为特征向量喂给九步协议 → 得到 τ/L/R/Ψ 裁定**。

```python
from tianci import Observation, run_heartbeat_with_protocol

res = run_heartbeat_with_protocol(Observation(label="基因/BRCA1", values=[55.0, 5.592, 8.0, 70.0]))
res["runtime"]    # 心跳输出（含 transmitter_triggered 等）
res["verdict"]    # 协议裁定（tau/L/R_state/psi/sigma_total）
res["features_used"]  # 六维监察 → 协议特征 的映射
```

六维 → 特征映射（monitor key → 特征名）：ρ→f_集中度，σ→f_离散度，δ→f_偏态，λ→f_峰均，C²→f_一致性(取 1-C²)，MΣ→f_波动。

---

## 7. 能力边界（诚实约束）

- **不代替平台动作**：本包只是技术特征实现，发布/点赞/评论由使用者执行。
- **不造假数据**：注册表 19.5% 覆盖率如实标注；评论原文、弹幕不属于任何接口能力，不编造。
- **不跨模态**：图生成、视频生成不属于算子流技术特征范围。
- **输出必须结构化可比较**：Ψ 输出与 τ/L/R 判定一一对应，任何调用方拿同样的输入应得到可复现的判定流程。

---

## 8. 文件地图

| 路径 | 内容 |
|---|---|
| `tianci/operator.py` | Operator dataclass（11字段+五件套校验+from_spec） |
| `tianci/registry.py` | 注册表（读 registry.json + audit 审计） |
| `tianci/data/registry.json` | 算子注册唯一事实源（自 v7.0 抽取） |
| `tianci/protocol.py` | 124 四模块九步 + 阈值 + 状态机 |
| `tianci/runtime.py` | 152 七器官运行时 V2.0.0.3 |
| `tianci/runtime_v2.py` | 三域适配器 + 暖启动 + Abel + 可视化（延迟导入） |
| `tianci/flow.py` | 心跳+协议缝合流 |
| `tianci/dag_route.py` | 102 天决策树 route() |
| `tianci/glossary.py` | 26 条中英术语锚定表 |
| `specs/operator-stream.md` | 本文件 |
| `specs/whitepaper-lineage.md` | 血统与里程碑 |
| `specs/anti-patterns.md` | AP-1~AP-5 反模式（190 反向方案） |
| `known-gaps.md` | 契约缺口与覆盖口径（19.5%） |