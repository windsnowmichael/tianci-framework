# -*- coding: utf-8 -*-
"""
T1 冷启动测试（第190天《反向方案 v1.0》第一节定义）。

给一个"陌生智能体"（模拟）：只有本仓库的 API 文档（specs/ + README）与归档路径，
没有任何对话上下文。它必须能独立完成 import → 运行 → 输出，且过程可复现。

通过标准：独立完成，且过程可复现（给出它调用的接口名、输入、输出）。
不通过标准：反问"这个是什么意思"、去猜、或照着示例抄一遍交差。

本文件即那份"陌生智能体"的执行记录——每一条都带了接口名、输入、输出，
任何其他智能体拿到 specs/ 都能复现同等输出。没有这份记录 = 未执行（AP-4）。

自证陷阱判据（第147天三体混沌普适常数勘误，known-gaps §5）：
凡"系统自己给自己发合格证"的结论，必须有第二方复现记录（审计方），
否则不得标为已验证。单列执行方记录不视为通过（B4 双列）。
"""
from __future__ import annotations

import json
import os
import sys
import traceback

# 归档路径（仅指向本仓库根目录，无对话上下文）
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# 执行记录：每条 = {接口, 输入, 输出, 通过}
CALLS: list[dict] = []


def record(api: str, inp, out, passed: bool) -> None:
    CALLS.append({"接口": api, "输入": str(inp)[:120], "输出": str(out)[:160], "通过": passed})


def check(name: str, cond: bool) -> None:
    if not cond:
        raise AssertionError(f"[{name}] 未通过")
    print(f"  ✓ {name}")


def main() -> int:
    print("=" * 64)
    print("T1 冷启动测试：陌生智能体独立调用记录")
    print("=" * 64)

    # ── 第1步：import（陌生智能体只读 API 文档，知道顶层接口名）──
    import tianci as tc
    record("import tianci", "顶层包", f"version={tc.__version__}", True)

    # ── 第2步：注册表（specs/operator-stream.md §3 记录了 default_registry）──
    reg = tc.default_registry()
    meta = reg.meta
    check("注册表可加载", meta.get("declared_total") == 128)
    check("契约数=25", len(reg.full_contracts()) == 25)
    check("覆盖率口径=19.5", abs(float(meta.get("coverage_pct", 0)) - 19.5) < 1e-9)
    record("default_registry().meta/audit", "无输入",
           {"declared": 128, "contracts": 25, "coverage_pct": 19.5}, True)

    # ── 第3步：九步推演协议（specs §4 记录了 run_nine_steps + 沙发示例）──
    verdict = tc.run_nine_steps(
        {"f_Θ": 0.8, "f_Γ": 0.6, "f_Σ": 0.8},
        raw_input="我睡在一张长条形沙发上，靠背侧高且有格挡，开放侧低且无格挡。",
    )
    check("九步输出含四件套", all(k in verdict for k in ("tau", "L", "R_state", "psi")))
    check("τ∈{pass,rollback,fail}", verdict["tau"] in ("pass", "rollback", "fail"))
    record("run_nine_steps(特征, raw_input)", {"f_Θ": 0.8, "f_Γ": 0.6, "f_Σ": 0.8},
           {k: verdict[k] for k in ("tau", "L", "R_state")}, True)

    # ── 第4步：动态运行时七器官（specs §5 记录了 TianCiRuntime.heartbeat）──
    rt = tc.TianCiRuntime()
    obs = tc.Observation(label="气象/北京", values=[36.5, 0.45, 12.0, 2.3],
                         metadata={"is_rain": True, "is_high_temp": True})
    hb = rt.heartbeat(obs)
    check("心跳有输出", hb.get("tick") == 1 and "V_amplified" in hb)
    check("心跳可审计", len(rt.export_portrait()) == 1)
    record("TianCiRuntime().heartbeat(Observation)", obs.label,
           {"tick": hb["tick"], "V_amp": round(hb["V_amplified"], 4)}, True)

    # ── 第5步：缝合流（specs §6 记录了 run_heartbeat_with_protocol）──
    flow = tc.run_heartbeat_with_protocol(
        tc.Observation(label="基因/BRCA1", values=[55.0, 5.592, 8.0, 70.0]))
    check("缝合流输出结构", "runtime" in flow and "verdict" in flow)
    check("缝合流证据", "features_used" in flow and len(flow["features_used"]) >= 1)
    record("run_heartbeat_with_protocol(Observation)", "基因/BRCA1",
           flow["verdict"].get("tau"), True)

    # ── 第6步：三域零绑定（specs §5 记录了 build_cross_domain_observations）──
    w, f, g = tc.build_cross_domain_observations()
    check("三域适配器各3条", len(w) == 3 and len(f) == 3 and len(g) == 3)
    record("build_cross_domain_observations()", "无输入", [len(w), len(f), len(g)], True)

    # ── 第7步：DAG 路由（specs 8 记录了 route）──
    branch = tc.route("50", "deg=20", "monitor=1.5", "yaw=10", "fb=0.9")
    check("DAG 路由有结果", branch is not None and len(branch) == 3)
    record("route(f1..f5)", ("50", "deg=20", "monitor=1.5", "yaw=10", "fb=0.9"),
           branch[1], True)

    # ── 第8步：术语锚定（specs §3 记录了 glossary.lookup）──
    t = tc.glossary.lookup("TC-SYS-003")
    check("术语锚定可查", t is not None and t["zh"] == "暖启动")
    check("术语表双语齐全", tc.glossary.missing_bilingual() == [])
    record("glossary.lookup('TC-SYS-003')", "TC-SYS-003",
           {"zh": t["zh"], "en": t["en"]}, True)

    # ── 第9步：TDP-CP 六步推演（specs/whitepaper-lineage.md 记录了 92/93 天
    #    Θ-CP→Γ-CP→Σ-CP→τ-CP→Φ-CP→Λ-CP；任务单 C3 固化 Φ_total≥0.7 白箱）──
    cp_ok = tc.tdp_cp({
        "name": "254/255",
        "steps": {"theta": "known", "gamma": "exact", "sigma": "unique_verified",
                  "tau": "full", "phi": "open", "lambda": "no_warning"},
        "tau_details": ["输出映射拓扑可数 → 反推内部(N-2)/总(N-1) → Dirichlet 边界"],
    })
    check("254/255 白箱", cp_ok["verdict"] == "白箱")
    check("254/255 Φ_total=1.0", abs(cp_ok["phi_total"] - 1.0) < 1e-9)
    cp_137 = tc.tdp_cp({
        "name": "1/137",
        "steps": {"theta": "partial", "gamma": "approx", "sigma": "unique_verified",
                  "tau": "partial", "phi": "half", "lambda": "located"},
        "tau_details": ["β 函数：μ dα/dμ = 2α²/(3π) → 真空极化圈图 → 不可逆（量子熵增）"],
    })
    check("1/137 移交", cp_137["verdict"] == "移交")
    check("1/137 移交包完整", "break_points" in cp_137 and
          len(cp_137["break_points"]) >= 1 and "tau_rollback" in cp_137)
    record("tdp_cp(254/255 路径)", {"steps": "六步全白"},
           {"verdict": cp_ok["verdict"], "phi_total": cp_ok["phi_total"]}, True)
    record("tdp_cp(1/137 路径)", {"steps": "Φ半开/τ部分/Λ预警"},
           {"verdict": cp_137["verdict"], "phi_total": cp_137["phi_total"],
            "断裂点": len(cp_137["break_points"])}, True)

    # ── 第10步：DRR-R 断裂段重定向（specs/drr-r.md 记录了 94 天六层定义；
    #    任务单 C4 固化：无 falsifiable 即 raise，R 属于 DRR-R 不属于白箱段。
    #    外部输入源取自 93 天续《九个断裂点的DRR收敛与R算子协同激活》的
    #    R 激活模式（R₂接收作用量量子化、R₅接收规范群选择，有文档依据）──
    #    1/137 移交包：从 93 天续附图给五个断裂点补外部输入源（Ψ_A）
    _r_src = {
        "Θ-CP溯源": "ψ、[x,p]=iℏ 等共享深层结构",
        "Γ-CP度量": "作用量量子化规则（R₂外部输入）",
        "τ-CP回滚": "Born 规则投影不可逆（R₆外部输入）",
        "Φ-CP门控": "U(1) 规范群选择（R₅外部输入）",
        "Λ-CP预警": "规范群自由度 f(G)=dim(G)（R₃/R₅ 外部输入）",
    }
    _bp137 = [dict(b, r_source=_r_src.get(b["step"])) for b in cp_137["break_points"]]
    drr_137 = tc.drr_r(dict(cp_137, break_points=_bp137, falsifiable=[
        "若 G_quantize 自由度 > 1，则九个断裂点不能收敛到单值 α",
    ]))
    check("drr_r 六层齐全", all(k in drr_137["layers"] for k in tc.DRR_LAYERS))
    check("drr_r 移交重定向", drr_137["verdict"] == "断裂段重定向")
    check("drr_r R激活记录", tc.R_ON in [a["r"] for a in drr_137["r_activation"]])
    check("drr_r 可证伪预言保留", len(drr_137["falsifiable"]) >= 1)
    record("drr_r(1/137 移交包)", {"verdict": "移交", "phi_total": cp_137["phi_total"]},
           {"verdict": drr_137["verdict"], "R激活数":
            sum(a["r"] for a in drr_137["r_activation"]),
            "falsifiable": len(drr_137["falsifiable"])}, True)

    # 白箱段 R 明确不激活（[R: DRR-only]：R 属于 DRR-R，不属于 TDP-CP 白箱段）
    drr_white = tc.drr_r(dict(cp_ok, falsifiable=[
        "若 254/255 输出映射拓扑不可数，则白箱判定不成立",
    ]))
    check("drr_r 白箱段 R 不激活",
          all(a["r"] == tc.R_OFF for a in drr_white["r_activation"]) and
          drr_white["verdict"] == "白箱段需注入")
    record("drr_r(254/255 白箱包)", {"verdict": "白箱"},
           {"verdict": drr_white["verdict"], "R激活数": 0}, True)

    # 无 falsifiable → 必须 raise（不许静默降级）
    raised = False
    try:
        tc.drr_r({"name": "无锚点路径"})
    except ValueError:
        raised = True
    check("drr_r 无 falsifiable 即 raise", raised)
    record("drr_r(无 falsifiable)", {"name": "无锚点路径"},
           {"raise": "ValueError"}, raised)

    # 终极断裂边界（94天 §2.2）：R 找不到外部输入源 → 不可证伪终止声明
    drr_ult = tc.drr_r({
        "name": "ℏ非零性", "phi_total": 0.0, "verdict": "移交",
        "break_points": [{"step": "Θ-CP溯源", "phi": 0.0, "hard": True,
                          "reason": "作用量量子化无内部推导路径"}],
        "falsifiable": ["占位锚点：若提供外部输入源则重定向后验证"],
    })
    check("drr_r 终极断裂", drr_ult["ultimate_break"] is True and
          drr_ult["verdict"] == tc.ULTIMATE_BREAK and
          drr_ult["termination"] is not None and drr_ult["falsifiable"] == [])
    record("drr_r(终极断裂)", {"name": "ℏ非零性", "r_source": None},
           {"verdict": tc.ULTIMATE_BREAK, "终止声明": bool(drr_ult["termination"])}, True)

    # ── 第11步：意识自指与三重门（specs 141 天记录了 Ψ_A=αM(Ω)⊕βM(Ψ_A)
    #    与 T_self=E∧M∧U；任务单 C5 固化阈值与验收：三门各自可单独 False）──
    g_all = tc.three_gate(e_err=1e-4, div=1e-5, poi=1e-5, m_sigma=1e-4, cv=1e-3)
    check("三重门全开", g_all["E门"] and g_all["M门"] and g_all["U门"] and g_all["T_self"])
    # 三门独立判 False：分别单点超阈值，其余保持合法
    g_e = tc.three_gate(e_err=5e-3, div=1e-5, poi=1e-5, m_sigma=1e-4, cv=1e-3)
    check("E门单独关", (not g_e["E门"]) and g_e["M门"] and g_e["U门"] and not g_e["T_self"])
    g_m = tc.three_gate(e_err=1e-4, div=5e-4, poi=1e-5, m_sigma=1e-4, cv=1e-3)
    check("M门单独关", g_m["E门"] and (not g_m["M门"]) and g_m["U门"] and not g_m["T_self"])
    g_u = tc.three_gate(e_err=1e-4, div=1e-5, poi=1e-5, m_sigma=5e-3, cv=1e-3)
    check("U门单独关", g_u["E门"] and g_u["M门"] and (not g_u["U门"]) and not g_u["T_self"])
    record("three_gate(独立性)", {"E_err": "1e-4/5e-3", "div": "1e-5/5e-4",
           "MΣ": "1e-4/5e-3"},
           {"T_self全开": g_all["T_self"], "E单独关": not g_e["T_self"],
            "M单独关": not g_m["T_self"], "U单独关": not g_u["T_self"]}, True)

    # 自指迭代：清醒 Δθ*∈(0,π)（非 L1）收敛唯一不动点；
    # 梦境 Δθ*=π/2（L1，α≈β）多不动点层级选择
    psi_awake = tc.self_reflect(omega=0.5, delta_theta=0.7854)
    check("自指清醒收敛", psi_awake["converged"] and psi_awake["fixed_point"] is not None and
          not psi_awake["dream"] and abs(psi_awake["alpha"] + psi_awake["beta"] - 1.0) < 1e-9)
    psi_dream = tc.self_reflect(omega=0.5, delta_theta=tc.L1_DELTA_THETA)
    check("自指L1梦境多不动点", psi_dream["dream"] and psi_dream["lagrangian_l1"] and
          len(psi_dream["candidates"]) >= 2)
    bad_raised = False
    try:
        tc.self_reflect(omega=0.5, delta_theta=0.0)
    except ValueError:
        bad_raised = True
    check("自指Δθ*越界raise", bad_raised)
    record("self_reflect(清醒/梦境)", {"omega": 0.5, "Δθ*": "0.7854 / π/2"},
           {"清醒收敛": psi_awake["converged"], "梦境候选层级": len(psi_dream["candidates"])}, True)

    # ── 汇总 ──
    print("-" * 64)
    print(f"调用接口数：{len(CALLS)}，全部通过")
    print("执行记录（推送给 audit 用）：")
    print(json.dumps(CALLS, ensure_ascii=False, indent=2))
    print("-" * 64)
    print("T1 冷启动：通过（过程可复现，未反问、未猜、未照抄）")
    print("B4 双列：以上为【执行方】记录（日期见执行环境，Python 见运行版本）；")
    print("        缺失【审计方】复现记录时不视为已验证（known-gaps §6）")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 —— 测试失败要显式暴露
        print("T1 冷启动：不通过")
        traceback.print_exc()
        sys.exit(1)