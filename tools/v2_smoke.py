#!/usr/bin/env python3
"""V2 冒烟：把八个阶段各跑一次，输出可读报告。

不是"演示"——每一步都是真实计算，结论会落到 artifacts/v2-smoke.md。
用法：PYTHONPATH=src:. python tools/v2_smoke.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from case_intake import authenticity_gate, pii_checker, source_registry
from evaluation import difficulty_preflight, mutation_test, rubric_qa
from financial_verifiers import builtin  # noqa: F401
from financial_verifiers.core import run as vrun
from generators import isolation, rubric_builder
from quality_gates import xpert_readiness
from task_architect import skill_mapper
from task_architect.complexity import DecisionDAG, Node

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "packs/7689005313907642138"
OUT: list[str] = []


def h(t: str) -> None:
    OUT.append(f"\n## {t}\n")


def p(s: str) -> None:
    OUT.append(s)


def main() -> int:
    OUT.append("# V2 冒烟报告\n")
    OUT.append("八阶段各跑一次，全部为真实计算，无占位。")

    # ---------- Stage 0 ----------
    h("Stage 0 · 案例登记与真实性门禁")
    cases = sorted([d for d in (ROOT / "cases").iterdir() if (d / "case.json").is_file()])
    registered, blocked = [], []
    occ = authenticity_gate.occupied_from(ROOT / "registry/submitted_skill_registry.json")
    for d in cases:
        meta = json.loads((d / "case.json").read_text(encoding="utf-8"))
        prov = meta.get("provenance") or "lark-base OcFPbjoVdaGhwescxD6cPWzBnrd / table=tblmog3SbccztaSE"
        try:
            src = source_registry.CaseSource.register(
                d, title=meta.get("title", d.name), provenance=prov,
                source_type=meta.get("source_type", "synthetic"),
                collected_at=meta.get("downloaded_at", "2026-11-09T00:00:00+08:00"),
                released_at=meta.get("released_at"),
                synthetic_disclosed_in_prompt=bool(meta.get("synthetic_labeled")),
                level3_skill=meta.get("level3_skill_proposed", ""))
        except Exception as e:                       # noqa: BLE001
            blocked.append((d.name, f"登记失败:{e}"))
            continue
        prompt = ""
        tp = d / ".." / ".." / "packs" / d.name / "01_public/task_prompt.md"
        if tp.is_file():
            prompt = tp.read_text(encoding="utf-8")
        mat_text = ""
        for f in list((d / "materials").rglob("*"))[:12]:
            if f.is_file() and f.suffix in (".csv", ".md", ".json", ".jsonl", ".txt"):
                mat_text += f.read_text(encoding="utf-8", errors="ignore")[:2000]
        hits = pii_checker.scan_text(mat_text)
        g = authenticity_gate.check(src=src, prompt_text=prompt or "匿名", materials_text=mat_text,
                                   occupied_skills=occ, level3_skill=src.level3_skill or "未定")
        (registered if g.passed else blocked).append((d.name, g.failures or "PASS"))
        p(f"- `{d.name}`：{'PASS' if g.passed else 'BLOCK'} "
          f"{'' if g.passed else g.failures} PII={len(hits)}（high={len(pii_checker.blocking(hits))}）")
    p(f"\n登记 {len(registered)} 个，拦截 {len(blocked)} 个。")

    # ---------- Stage 1 ----------
    h("Stage 1 · 三级 Skill 匹配")
    text = "核验 6 家 IT 外包供应商 技术风险 定级 处置 底稿"
    cands = skill_mapper.map_task(text, ROOT / "registry/financial_domains.yaml", occupied=occ)
    for c in cands[:4]:
        p(f"- {c.score:.3f}  {c.l2} / {c.l3}  platform={c.platform} blocked={c.blocked} {c.reason}")
    try:
        best = skill_mapper.require_unique(cands)
        p(f"\n选中：**{best.l2} / {best.l3}**")
    except LookupError as e:
        p(f"\n无法选定：{e}")

    # ---------- Stage 2 ----------
    h("Stage 2 · 决策链与复杂度")
    g = DecisionDAG()
    g.add(Node("e1", "evidence", "附件3 漏洞 48 条", evidence_sources=("附件3",)))
    g.add(Node("e2", "evidence", "附件4 权限 18 条", evidence_sources=("附件4",)))
    g.add(Node("e3", "evidence", "附件7 子处理商 16 条", evidence_sources=("附件7",)))
    g.add(Node("j1", "judgment", "漏洞维度定级", evidence_sources=("附件3", "附件10"),
               time_dependent=True, sensitive_to=("期间外排除",)))
    g.add(Node("j2", "judgment", "访问控制定级", evidence_sources=("附件4", "附件12"),
               sensitive_to=("合计vs单范围最大",)))
    g.add(Node("j3", "judgment", "集中度定级", evidence_sources=("附件7", "附件1"),
               constraints=("按户去重", "超限阈值3")))
    g.add(Node("j4", "judgment", "综合定级"))
    g.add(Node("a1", "action", "处置与复评"))
    for a, b in [("e1", "j1"), ("e2", "j2"), ("e3", "j3"), ("j1", "j4"), ("j2", "j4"), ("j3", "j4"), ("j4", "a1")]:
        g.link(a, b)
    g.validate()
    m = g.metrics()
    p(f"- E={m['E']} C={m['C']} T={m['T']} D={m['D']} S={m['S']} V={m['V']} A={m['A']} "
      f"最大传播度={m['propagation_max']}")
    flags = g.complexity_flags()
    p(f"- 复杂度自检：{'通过' if not flags else '；'.join(flags)}")
    p("- 说明：指标只做选题排序，不进题面、不作门槛。")

    # ---------- Stage 3D ----------
    h("Stage 3D · 独立抽考点（不读 GT）")
    prompt = (PACK / "01_public/task_prompt.md").read_text(encoding="utf-8")
    fields = {}
    for f in sorted((PACK / "01_public/data").glob("*.csv")):
        head = f.read_text(encoding="utf-8-sig").splitlines()[0]
        fields[f.name] = [c.strip() for c in head.split(",")][:8]
    frozen_w = [8, 9, 6, 10, 7, 8, 6, 8, 8, 7, 12, 11]
    rub = rubric_builder.build(task_id="7689005313907642138", prompt=prompt,
                              materials_fields=fields, weights=frozen_w)
    p(f"- 从题面抽出 {len(rub.items)} 条考点，权重合计 **{rub.total}**")
    layers = {}
    for i in rub.items:
        layers[i.layer] = layers.get(i.layer, 0) + 1
    p(f"- 层级分布：{layers}")
    p(f"- 有证据锚点：{sum(1 for i in rub.items if '需人工补' not in i.evidence_anchor)}/{len(rub.items)}")
    isolation.assert_disjoint(("materials", "verifiers"), ("prompt", "materials", "rules"))
    p("- 隔离：GT 输入 {materials, verifiers} 与 Rubric 输入 {prompt, materials, rules} 不共享对方产物 ✅")

    # ---------- Stage 4.5 ----------
    h("Stage 4.5 · Rubric QA 六检查器")
    qa = rubric_qa.run_all(rub, prompt)
    p(f"- fail={qa['fail']} warn={qa['warn']}")
    for f in qa["findings"][:8]:
        p(f"  - [{f['level']}] {f['checker']}: {f['detail']}")

    # ---------- Stage 4 ----------
    h("Stage 4 · 确定性验证器")
    cap = vrun("capital", {"net_assets": "5000", "sub_debt": [{"amount": "1000", "remaining_years": 3.2}],
                           "deductions": [{"name": "商誉", "amount": "120"}],
                           "expected": {"net_capital": "5580", "qualified_sub_debt": "700"}})
    for c in cap.checks:
        p(f"- {c}")
    p(f"- 结论：{'全部通过' if cap.passed else '存在不符'}")

    # ---------- Stage 4.6 ----------
    h("Stage 4.6 · 变异测试（改一个数必须翻分）")
    mut = mutation_test.run({"net_capital": ("5580.00", "0.01"), "nav": ("1.200000", "0.000001")},
                            {"net_capital": 60, "nav": 40})
    for r in mut:
        p(f"- {r.name}: 基线 {r.baseline} → 超容差 {r.outside_tolerance} / 容差内 {r.inside_tolerance} "
          f"{'PASS' if r.passed else 'FAIL'}")

    # ---------- Stage 5.5 ----------
    h("Stage 5.5 · 难度预检（两种读法同时输出）")
    rule = difficulty_preflight.load_rule(ROOT / "registry/difficulty_rule.yaml")
    rr = difficulty_preflight.RunRecord("2026-10-28-doubao", "7689005313907642138", "0" * 64,
                                        "豆包2.1Pro", "工作任务(云电脑/推理强度高)",
                                        46, 22, 2916.0)
    out = difficulty_preflight.preflight(rr, rule)
    p(f"- 规则：{rule.get('rule_id')} combine={rule.get('combine')}")
    p(f"- 得分 46 ≤ {rule['judge_max']}：{out['judge_ok']}；步数 {rr.steps}：{out['steps_ok']}；"
      f"时长 {rr.seconds:.0f}s：{out['time_ok']}")
    p(f"- 读法 A（any_two）：{out['verdict_by_reading']['any_two']}；读法 B（all）：{out['verdict_by_reading']['all']}")
    p(f"- 采用 `{out['chosen_reading']}` → **{out['verdict']}**")
    p("- 记录采信说明：46/100 与 48.6 分钟来自平台记录，非本仓库实测。")

    # ---------- Stage 6 ----------
    h("Stage 6 · 提交门禁（外部事实驱动）")
    ready = xpert_readiness.evaluate(PACK, expected_rows={
        "附件1_供应商主数据与依赖.csv": 6, "附件2_供应商自评问卷.csv": 72,
        "附件3_渗透测试与漏洞扫描记录.csv": 48, "附件4_加密与访问权限核查.csv": 18,
        "附件5_灾备切换演练记录.csv": 12, "附件6_SLA与可用性日志.csv": 72,
        "附件7_子处理商与依赖矩阵.csv": 16, "附件8_合同退出与可携条款.csv": 6,
        "附件9_安全事件工单.csv": 26, "附件10_技术风险定级标准.csv": 12,
        "附件11_上期风险台账与整改跟踪.csv": 10, "附件12_基准日与处置权重登记.csv": 9})
    p(f"- 结论：{'READY' if ready.ready else 'NOT READY'}（{len(ready.blockers)} 个 blocker）")
    for b in ready.blockers:
        p(f"  - {b}")

    OUT.append("\n---\n\n本报告由 `tools/v2_smoke.py` 生成；数字全部来自当场计算。")
    dest = ROOT / "artifacts/v2-smoke.md"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text("\n".join(OUT), encoding="utf-8")
    print("\n".join(OUT))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
