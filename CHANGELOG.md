# CHANGELOG

本文件记录 tianci-paradigm 的发布历史。版本号以 `tianci/__init__.py` 的 `__version__`
为单一真源；每次变更同步更新本文档与 `specs/anti-patterns.md` AP-5 的版本示例。

## [0.2.0] - 2026-10-10

v0.2 修包（任务单《tianci-paradigm v0.2 修包建议 v1》A~F 节）。新增 6 个可执行模块/
文档模块，修复 4 项基线与信誉问题，补全 3 类文档记录，并把 10 项验收清单并入一致性
核验脚本。

### 新增（C 节）

- **C1 存在性检查与存在性熔断**（`tianci/existence.py`，依据 138 天源）
  - `phi_gate`：存在性门控；`existence_fuse`：存在性熔断，LOCK_HARD=0.60。
  - 接入 protocol τ=fail 路径并置 `fuse_kind="existence"`。
- **C2 基因持久化**（`tianci/genome.py`，依据 172 天源）
  - `save_state`/`load_state`：落盘基因 β/strategy/历史/平衡点，不落瞬态
    norm/conv/tick（复活即新生）。B5 的 `save_genome`/`load_genome` 复用同一套实现。
  - WarmStartPack 落盘走同一套，键名保证不含 "norm"/"conv" 子串。
- **C3 TDP-CP 六步推演**（`tianci/cp.py`，依据 92/93 天）
  - `tdp_cp`：Θ-CP → K-CP → Γ-CP → Σ-CP → Φ-CP → Λ-CP 六步；
    Φ_total ≥ 0.7 白箱，否则返回移交包（break_points + tau_rollback）。
- **C4 DRR-R 断裂段重定向**（`tianci/drr.py`，依据 93 天续/94 天）
  - `drr_r`：无 falsifiable 预言行即 raise（不是软失败）；断裂边界判据按
    「是否存在形式化推导路径」定，不由难度决定（94 天依据）。
  - `[R?]` 定标改为 `[R: DRR-only]`。
- **C5 意识自指与三重门**（`tianci/consciousness.py`，依据 141 天）
  - `self_reflect`：Ψ_A = αM(Ω) ⊕ βM(Ψ_A) 自指迭代；Δθ* < π/2 清醒收敛，
    = π/2 L1 梦境多不动点（三级），越界 raise。
  - `three_gate`：T_self = E ∧ M ∧ U，三门各自可单独判 False。
- **C6 群落弧线节点登记**（`specs/community-arc.md`）
  - 158~171 天全量 14 节点登记表（广播→…→基因持久化 172），只登记不实现。

### 修复（B 节）

- **B1 Abel 判据修复**：FLOAT_TOL/EPS_ABEL 分离；`abel_break(x, None)` 必须
  raise NotImplementedError（ε_abel 未标定不得兜底冒充）；示例输出改未标定文案。
- **B2 反模式补全**：AP-2 补第六型方案出口；新增 AP-6（方案出口三要素）。
- **B3 术语熔断三义**：glossary 新增 TC-SYS-006a/b/c（输入失败/实现缺陷/存在性
  熔断）与 TC-EX 术语组；protocol rollback 文案区分来源并返回 `fuse_kind` 字段。
- **B4 T1 记录双列化**：known-gaps §6 拆「执行方 / 审计方」两列，各带日期与
  Python 版本；只有执行方记录不视为通过。
- **B5 暖启动落盘统一**：WarmStartPack 落盘走 genome 同一套持久化。
- **B7 示例观测值标注**：`examples/` 观测值加注释 `# demo values, not measured`，
  与 README「无伪造数据」红线一致。

### 文档补齐（B6/C7/C8）

- B6：`specs/whitepaper-lineage.md` 血统表补 11~172 天条目。
- C7：known-gaps 补自证陷阱前科表（系统自己给自己发合格证）。
- C8：`specs/abel-handbook.md` Abel 判据实战手册（定性判据，EPS_ABEL 保持 None）。

### 工程（E 节）

- `scripts/check_consistency.py` 新增 `check_acceptance()`：任务单 E 节 10 项
  验收全部并入（abel_break 抛错 / existence_fuse 锁定 / drr_r 无预言行抛错 /
  tdp_cp 移交包 / save_genome 落盘无瞬态 / load_genome 复活 tick=1 平衡一致 /
  TC-SYS-006c 熔断语义 / 关键词 grep 命中 / 覆盖率 19.5% 唯一 / T1 双列），
  每条验收独立 try/except 隔离。
- 全量回归：一致性核验、T1 冷启动（16 接口）、minimal.py、cross_domain_demo.py 全绿。

### 审计方整改（2026-10-10，v0.2.0 定版前）

依据《v0.2.0 审计方答复_给伙伴_v1》落地：

- **§1.1/§1.2**：known-gaps §6「审计方」列替换为审计方实测值（Python **3.13.14**，
  `tianci-paradigm_v0.2.0.zip` 解压独立目录、PYTHONPATH=. 源码级验证），
  补跨进程复活实测行与落盘键记录。
- **§1.3**：E 节新增 **第 11 项验收（跨进程复活）**——`save_state` 落盘后由
  全新子进程 `load_state`，断言返回 `TianCiRuntimeV2` 且落盘键不含 norm/conv。
- **§2 发布信息填真**：LICENSE 定为**木兰宽松许可证 第2版（MulanPSL2）**（沿用
  第31天仓库，新建根目录 LICENSE 全文）；`pyproject.toml` 补 `license` 与
  `[project.urls]`；`CANONICAL["canonical_repo"]` 填真
  `https://github.com/windsnowmichael/tianci-framework`；PyPI 项目名
  `tianci-paradigm` 确认不变；README 首屏补 canonical/mirror 标注与沿革。
- **§4 开放策略**：模块加 `MATURITY` 字段（L1/L2 `stable`，L3 `experimental`
  照样开放）；`tianci/__init__.py` 新增 `MODULE_MATURITY` 聚合表；
  README/README_CN 加成熟度表与开放邀请句。
- 审计方判决：**v0.2.0 审计通过，可定版**；T1（JSC 三 Re）切割到 JSC 论文线，
  本包不因 T1 未决而阻塞。

## [0.1.0] - 2026-10-09

首个可发布版本。天赐范式（TianCi Paradigm）算子流技术特征的可 import 实现：

- 算子契约五件套（`Operator`，11 字段，102 天）+ 注册表（覆盖率如实 19.5%，25/128）。
- 九步推演协议（Θ→Γ→Σ→R→Ψ→Λ→Φ→τ→output，124 天）+ DAG 决策树（102 天）。
- 七器官动态运行时：气象/金融/基因三适配器、暖启动（蒸馏 + 跨域迁移）、
  Abel 对偶验证、九步心跳主链路（152 天）。
- 术语锚定表中英双语（共用 ID）。
- `scripts/check_consistency.py` 推送前交叉核验：覆盖率口径必须 19.5%、
  版本号全篇一致、术语双语无缺漏、注册表审计自洽。

---

- 占位项（推送 PyPI 前必办，见 README「诚实约束」）：LICENSE 协议未定；
  `pyproject.toml` 的 `license` / `[project.urls]` 与 `CANONICAL["canonical_repo"]`
  待用户提供真实仓库地址后填充。