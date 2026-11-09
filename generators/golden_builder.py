"""Stage 3C · 标准答案生成（独立于 Rubric）。

三层 GT 一起产出，且每层都必须指向可核对的来源：
  Narrative GT   —— 专业意见（由数值结论拼装，不自由发挥）
  Calculation GT —— 全部由 `financial_verifiers` 计算，Decimal 精确
  Evidence GT    —— 每个数值挂 文件#字段 锚点

**输入里没有 rubric**：传进来会直接抛 IsolationError（见 `isolation.seal`）。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from financial_verifiers.core import Check, run

from . import isolation

DECLARED_INPUTS = ("materials", "verifiers")


@dataclass
class GtSpec:
    task_id: str
    verifiers: list[dict] = field(default_factory=list)   # [{"name","params","label"}]
    conclusions: list[str] = field(default_factory=list)  # 人工给定的结论句式模板


def build(*, task_id: str, materials_dir: str | Path, spec: GtSpec,
          out_dir: str | Path = "artifacts/golden_responses") -> dict:
    if "rubric" in DECLARED_INPUTS:                     # 防御性断言
        raise isolation.IsolationError("GT 不得读取 rubric")
    materials_dir = Path(materials_dir)
    results, checks = [], []
    for v in spec.verifiers:
        r = run(v["name"], v["params"])
        results.append({"label": v.get("label", v["name"]), "verifier": v["name"],
                        "passed": r.passed, "checks": [c.__dict__ | {"expected": str(c.expected),
                                                                     "actual": str(c.actual),
                                                                     "tolerance": str(c.tolerance)}
                                                        for c in r.checks]})
        checks.extend(r.checks)

    calc = [{"name": c.name, "value": str(c.actual), "anchor": c.anchor, "passed": c.passed}
            for c in checks]
    narrative = spec.conclusions or [
        f"{c.name}：{c.actual}" + ("" if c.passed else "（与预期不符，须复核）") for c in checks]
    evidence = sorted({c.anchor for c in checks if c.anchor})

    gt = {"task_id": task_id, "narrative": narrative, "calculation": calc,
          "evidence": evidence, "verifier_runs": results,
          "all_passed": all(c.passed for c in checks)}

    out = Path(out_dir) / task_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "golden_response.json").write_text(json.dumps(gt, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    lines = [f"# 标准答案 · {task_id}", "", "## Narrative GT", ""]
    lines += [f"- {n}" for n in narrative]
    lines += ["", "## Calculation GT", "", "| 项 | 值 | 锚点 |", "|---|---:|---|"]
    lines += [f"| {c['name']} | {c['value']} | {c['anchor']} |" for c in calc]
    lines += ["", "## Evidence GT", ""] + [f"- `{e}`" for e in evidence]
    lines += ["", "> 数值全部由 `financial_verifiers` 计算；本文件生成时未读取冻结考点。"]
    (out / "golden_response.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    isolation.seal("gt", DECLARED_INPUTS,
                   {"materials": materials_dir, "verifiers": "financial_verifiers/core.py"},
                   out)
    return gt


def cross_check(gt: dict, *, expected: dict[str, str]) -> list[Check]:
    """与冻结考点里的期望值交叉核对（这是核对，不是生成）。"""
    got = {c["name"]: c["value"] for c in gt["calculation"]}
    out = []
    for name, exp in expected.items():
        if name not in got:
            out.append(Check(name, exp, "MISSING", note="GT 缺少该数值"))
            continue
        out.append(Check.make(name, exp, got[name], tol="0.01", anchor="GT vs 冻结考点"))
    return out
