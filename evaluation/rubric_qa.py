"""Stage 4.5 · Rubric QA：六个自动检查器。

对应改造建议里的 Rubric QA Engine：
  duplicate        两条考点是否在查同一件事
  coverage         题面每条核心要求是否有对应考点
  evidence         每题是否有可定位的附件/字段锚点
  tolerance        金额/日期/比例/单位的精度是否一致
  alternative      合理替代写法是否被判等价（误杀检测）
  core_failure     Gate 是否真的关联任务关键用途失效
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from generators.rubric_builder import Rubric, parse_requirements

DIGIT = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class Finding:
    checker: str
    level: str      # fail | warn
    detail: str


def duplicate(r: Rubric, threshold: float = 0.7) -> list[Finding]:
    out = []
    norm = [(i.id, set(DIGIT.sub("#", i.statement))) for i in r.items]
    for a in range(len(norm)):
        for b in range(a + 1, len(norm)):
            A, B = norm[a][1], norm[b][1]
            if not A or not B:
                continue
            j = len(A & B) / len(A | B)
            if j >= threshold:
                out.append(Finding("duplicate", "fail",
                                   f"{norm[a][0]} 与 {norm[b][0]} 重合度 {j:.2f}，疑似查同一件事"))
    return out


def coverage(r: Rubric, prompt: str) -> list[Finding]:
    reqs = parse_requirements(prompt)
    if not reqs:
        return [Finding("coverage", "fail", "题面无编号交付要求，无法核对覆盖")]
    out = []
    for no, txt in reqs:
        if not any(txt[:12] in i.statement or i.statement[:12] in txt for i in r.items):
            out.append(Finding("coverage", "fail", f"题面第{no}条无对应考点：{txt[:40]}"))
    return out


def evidence(r: Rubric) -> list[Finding]:
    out = []
    for i in r.items:
        if not i.evidence_anchor or "需人工补" in i.evidence_anchor:
            out.append(Finding("evidence", "fail", f"{i.id} 无证据锚点"))
    return out


def tolerance(r: Rubric) -> list[Finding]:
    out = []
    for i in r.items:
        t = i.tolerance or ""
        if not t:
            out.append(Finding("tolerance", "fail", f"{i.id} 未写容差"))
        elif DIGIT.search(t) is None and "二值" not in t and "整数" not in t:
            out.append(Finding("tolerance", "warn", f"{i.id} 容差表述含糊：{t}"))
        elif "整数" not in t and "二值" not in t and not re.search(r"\d", t):
            out.append(Finding("tolerance", "warn", f"{i.id} 容差缺少数值"))
    return out


def alternative(r: Rubric) -> list[Finding]:
    out = []
    for i in r.items:
        if not i.accepted_alternatives:
            out.append(Finding("alternative", "warn",
                               f"{i.id} 未登记合理替代写法，可能误杀等价答案"))
    return out


def core_failure(r: Rubric) -> list[Finding]:
    out = []
    for i in r.items:
        if i.layer == "L1" and not i.zero_example:
            out.append(Finding("core_failure", "fail",
                               f"{i.id} 是 L1 核心结论考点但没有 0 分反例，Gate 无法关联关键用途失效"))
    return out


def run_all(r: Rubric, prompt: str = "") -> dict:
    fs: list[Finding] = []
    fs += duplicate(r)
    if prompt:
        fs += coverage(r, prompt)
    fs += evidence(r) + tolerance(r) + alternative(r) + core_failure(r)
    fails = [f for f in fs if f.level == "fail"]
    return {"findings": [f.__dict__ for f in fs], "fail": len(fails), "warn": len(fs) - len(fails),
            "ok": not fails}
