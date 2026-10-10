# -*- coding: utf-8 -*-
"""
tianci.glossary —— 中英术语锚定表（每个术语唯一 ID，中英共用）。

源：190 反向方案 v1.0 第四节「双语会制造第 6 例起的同名不同义」。
硬要求：每个术语给唯一 ID，中英两列共用同一 ID；
不许出现只有中文或只有英文的术语条目。
"""
from __future__ import annotations
MATURITY = "stable"   # 成熟度（审计方 2026-10-10 定标：L1/L2 stable，L3 experimental 照样开放）

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class GlossaryTerm:
    """一条术语锚定：ID / 中文 / 英文 / 定义 / 反例或前科 / 首次出现。"""

    id: str
    zh: str
    en: str
    definition: str
    caution: str = ""          # 反例 / 前科 / 同名不同义警示
    first_seen: str = ""       # 首次出现：第N天 或 章节

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "zh": self.zh,
            "en": self.en,
            "definition": self.definition,
            "caution": self.caution,
            "first_seen": self.first_seen,
        }


TERMS: List[GlossaryTerm] = [
    # ---- 算子流核心符号 ----
    GlossaryTerm("TC-INF-001", "感知", "Theta(-perception)", "外部信号进入系统的唯一端口；只接收信号，不判断业务。",
                 "与数学 theta 函数、统计参数 θ 同名不同义", "第115天方法论审计"),
    GlossaryTerm("TC-INF-002", "锚定", "Xi(-anchoring)", "把输入翻译为框架目标问题集合 G。",
                 "与 ξ(初始化)、ξ^rv(随机变量) 三义共存，引用时必须带下标或 ID", "第115天方法论审计"),
    GlossaryTerm("TC-INF-003", "度量", "Gamma(-metric)", "特征与基准（历史案例库或理论基准）的偏差向量 D。",
                 "Γ 基准必须是自指基准，否则致说谎者悖论（125 天验证）", "第115天方法论审计"),
    GlossaryTerm("TC-INF-004", "量化", "Sigma(-uncertainty)", "把偏差向量 D 量化为单一不确定性值 Σ_total = (Σd_i²)^(1/2)/√n ∈ [0,1]。",
                 "Σ 与求和符号同字；在天赐范式中必须带下标或语义限定", "第115天方法论审计"),
    GlossaryTerm("TC-INF-005", "预警", "Lambda(-alert)", "按 Σ_total 检查预警等级：<0.3 绿 / 0.3-0.6 黄 / ≥0.6 红。",
                 "Λ 阈值 0.3/0.6 来自理论推演而非实证标定，v0.2 可能调整", "第124天技术协议"),
    GlossaryTerm("TC-INF-006", "判定", "tau(-verdict)", "综合 Σ_total 与预警等级输出 τ ∈ {pass, rollback, fail}。",
                 "与软件工程 circuit breaker 同字不同义；τ=pass 只证明自洽，不等于被执行（AP-4）", "第124天技术协议"),
    GlossaryTerm("TC-INF-007", "自指", "Psi(-self-reference)", "生成自指描述：系统陈述自身状态与判定结论。",
                 "自指必须锚定 Γ 基准，否则陷入说谎者悖论", "第124天技术协议"),
    GlossaryTerm("TC-INF-008", "门控", "Phi(-gate)", "布尔完备逻辑门阵列，自动从 metadata 探测条件做 AND/OR/NOT/XOR。",
                 "Φ 门控需按领域特征向量与算子版本评估透明度", "第102天最小化技术特征"),
    GlossaryTerm("TC-R-001", "状态机", "R(-state)", "按 τ 更新系统状态：pass→PASSIVE / rollback→ACTIVE / fail→EMERGENCY。",
                 "R 是调节算子，任意阶段均可被触发切换状态", "第124天技术协议"),

    # ---- 系统级术语 ----
    GlossaryTerm("TC-SYS-001", "初始化", "xi(-init)", "从混沌态 U 生成标准初始态 S₀（归一化 ‖S₀‖=1）。",
                 "ξ 三义之一：初始化算子 / 随机变量 ξ^rv / 锚定 Ξ，必须区分", "第152天动态运行时"),
    GlossaryTerm("TC-SYS-002", "观测", "zeta", "从状态 S_t 与噪声协方差 Σ 生成观测值 O_t。",
                 "ζ 与 Zeta 函数无关联", "第152天动态运行时"),
    GlossaryTerm("TC-SYS-003", "暖启动", "warm start", "把源机器画像蒸馏成可迁移初值包（平衡点/放大尾迹/突触尾迹/参数），注入新机器。",
                 "已有前科：189 的 WARMUP_STATIC 是数值模拟预热步数，与 152 的暖启动同名不同义，强制区分两义", "第152天第二篇"),
    GlossaryTerm("TC-SYS-004", "黑启动/初值归零", "cold start / zeroing", "新机器从零初始态启动，不继承任何画像记忆；190 新增概念。",
                 "尚无旧前科；英文名本次定名并锁 ID", "第190天"),
    GlossaryTerm("TC-SYS-005", "算子", "operator", "带接口契约的可调用单元（输入域/输出域/前置条件/后置保证四件套）。",
                 "与编程语言 operator、数学 operator 三方冲突，必须带 ID 或上下文限定", "第102天"),
    GlossaryTerm("TC-SYS-006a", "熔断·放大电路发散截断", "circuit break / amp-cutoff", "放大电路发散时截断并锁定上一状态（第152天运行时七器官之一）。",
                 "与软件工程 circuit breaker 同字不同义；仅指运行时放大电路的正反馈发散保护，与 τ 判定、存在性熔断三义并列", "第152天动态运行时"),
    GlossaryTerm("TC-SYS-006b", "熔断·τ判定fail", "tau-fail", "第7步 τ 判定为 fail：Σ_total≥0.6 红档或 DAG 有环 / 连续3次红色预警时强制降级。",
                 "只陈述协议判定结果，不描述物理截断动作；与 006a / 006c 三义并列，引用必须带独立 ID", "第124天技术协议"),
    GlossaryTerm("TC-SYS-006c", "存在性熔断", "existence fuse", "第138天：存在撤销 → 回滚 → 减步（dt*=0.5）→ 重燃。η>LOCK_HARD=0.60 即触发 S1 锁定。",
                 "与 τ 判定 fail 同链不同义：fail 是判定，存在性熔断是 fail 之后的恢复动作序列，含回滚与重燃", "第138天存在性熔断"),
    GlossaryTerm("TC-EX-001", "毒丸公式", "poison-pill formula", "Φ=0 时系统逻辑矛盾锁死（第11天源码实测）：公式自身拒绝演化，杜绝自证合格。",
                 "与金融毒丸计划同字不同义；毒丸是元层自毁式守卫，不是业务异常", "第11天数学毒丸公式"),
    GlossaryTerm("TC-EX-002", "存在性检查（Φ）", "existence check (Phi)", "∇_μ ℒ_eff = λ·Φ(Con(ZFC+¬CH))：Φ 无量纲逻辑门，λ 负载量纲；\"＝\"为语义门控，非数值等式。",
                 "与 TC-INF-008 的 Φ 门控同符号两义：INF-008 是日志驱动布尔门阵列，EX-002 是存在性一致性门；引用必须带 ID", "第138天"),
    GlossaryTerm("TC-EX-003", "存在撤销", "existence revoke", "Φ=0（悖论）时撤销正在演化的存在性声明，回到上一可信状态。",
                 "与 rollback 同义近但层级不同：存在撤销是元层门控动作，rollback 是九步协议输出；勿混用口径", "第138天存在性熔断"),
    GlossaryTerm("TC-EX-004", "重燃", "reignition", "S2 状态：η 回落至安全带（<WARN_HI 或滞回下沿）后，以减半小步长重新演化。",
                 "与电路重启、物理复燃/锁相同名不同义；指演化空间中的减步重燃，重燃后仍受 Φ 门监护", "第138天存在性熔断"),
    GlossaryTerm("TC-EX-005", "M-Dim 元层门控", "M-Dim meta-layer gating", "元层模式量纲归位规则：元层式等式 \"＝\" 是语义门控而非数值等式，量纲归位后才可数值化。",
                 "只适用于元层模式推演，不直接下放到九步协议内层数值运算", "第138天 M-Dim 规则"),
    GlossaryTerm("TC-SYS-007", "降调", "downgrade", "本体系特定制度：章节内编号条目，遇 `#` / ``` / --- 无条件停止。",
                 "不可直译；与乐理/股市降调不同义，须写定义+扫描口径", "第188天以降复盘线"),

    # ---- 运行时七器官 ----
    GlossaryTerm("TC-ORG-001", "半导体单向导通", "Diode#96", "格式净化层：拦截空标签/空向量/NaN/Inf，不做价值判断。",
                 "负值信号默认放行（温度/收益率/基因差等负值业务）", "第152天动态运行时"),
    GlossaryTerm("TC-ORG-002", "放大电路", "Amp#95", "带记忆的正反馈：Γ(t) = Θ(t) + α·Γ(t-Δt)，超阈值截断锁定。",
                 "α 可被元引擎补丁自动降低（自愈闭环）", "第152天动态运行时"),
    GlossaryTerm("TC-ORG-003", "拉格朗日点突触", "R_Lagrange", "动态平衡点：感知偏离自动调频，平衡点向信号方向迁移。",
                 "与拉格朗日力学无直接关系，取动态平衡语义", "第152天动态运行时"),
    GlossaryTerm("TC-ORG-004", "发报机模式", "Lambda_Bombe", "六维监察（ρ/σ/δ/λ/C²/MΣ）任一越界即主动发报并附带根因。",
                 "监察值从信号向量本身统计推导，不依赖业务假设", "第152天动态运行时"),
    GlossaryTerm("TC-ORG-005", "元系统生成引擎", "Meta#97", "发报机触发后自动回溯画像、识别根因、生成并（V2 起）回填补丁。",
                 "V2.0.0.3 只生成建议；V2.1.0.0 起补丁真正修改机器参数", "第152天动态运行时"),
    GlossaryTerm("TC-ORG-006", "意识动力学画像", "Portrait#98", "记录机器从诞生到现在的全部轨迹（心跳/门切换/发报/补丁/输出），可审计可迁移。",
                 "画像不是日志备份，是可迁移的初值", "第152天动态运行时"),

    # ---- 协议四模块 ----
    GlossaryTerm("TC-PROTO-001", "算子注册表", "operator registry", "为算子建立分类索引与语义边界（v7.0 128 算子，25 全契约，覆盖率 19.5%）。",
                 "契约覆盖率必须如实标注，不得虚报", "第124天技术协议"),
    GlossaryTerm("TC-PROTO-002", "输入域规范", "input domain spec", "定义可处理（文本/实验数据/理论陈述/设计方案/感官描述）与不可处理输入类型。",
                 "输入无法映射到任何已知算子语义域时返回 τ=rollback", "第124天技术协议"),
    GlossaryTerm("TC-PROTO-003", "推演协议", "inference protocol", "Θ→Γ→Σ→Λ→τ→Ψ 的九步标准调用流程，分读取/判定/输出三阶段。",
                 "若 Con 监察发现 DAG 有环，τ 强制降级为 fail", "第124天技术协议"),
    GlossaryTerm("TC-PROTO-004", "输出域规范", "output domain spec", "标准输出格式 {τ, L, R_state, Ψ描述, 算子调用日志}，三种判定各有输出语义。",
                 "输出必须结构化、可比较", "第124天技术协议"),
]


def lookup(query: str, as_dict: bool = True) -> Optional[Dict[str, Any]]:
    """按 ID / 中文 / 英文 查询。

    默认返回 dict（可 JSON 化，冷启动友好）；as_dict=False 返回 GlossaryTerm。
    """
    q = query.strip()
    for t in TERMS:
        if t.id == q or t.zh == q or t.en == q or q in t.en:
            return (t.to_dict() if as_dict else {"_raw": t})
        # 字母不敏感匹配英文（如 sigma → Sigma）
        if q.lower() and t.en.lower().startswith(q.lower()):
            return (t.to_dict() if as_dict else {"_raw": t})
    return None


def lookup_term(query: str) -> Optional[GlossaryTerm]:
    """原始 dataclass 查询（需要访问字段对象时用）。"""
    r = lookup(query, as_dict=False)
    return r["_raw"] if r else None


def all_terms() -> Dict[str, Any]:
    return {t.id: t.to_dict() for t in TERMS}


def missing_bilingual() -> List[str]:
    """完整性检查：缺中文或缺英文的术语 ID 列表（不应有）。"""
    return [t.id for t in TERMS if not t.zh.strip() or not t.en.strip()]