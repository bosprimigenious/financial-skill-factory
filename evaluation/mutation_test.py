"""Stage 4.6 · 评分标准变异测试（Rubric Mutation Test）。

目的：证明"改一个关键数，分数必须掉；改在容差内，分数不该掉"。
如果改关键结果后判分不变，这条考点就不可靠。

`scorer` 由调用方注入（真实判分器或本模块的 `tolerance_scorer` 沙盘）。
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from financial_verifiers.core import D, q


def tolerance_scorer(expected: dict[str, tuple[str, str]], weights: dict[str, int]) -> callable:
    """按容差判定的沙盘评分器：|actual-expected| <= tol 得分，否则 0。"""
    def score(values: dict[str, str]) -> int:
        total = 0
        for name, (exp, tol) in expected.items():
            if name not in values:
                continue
            if abs(q(values[name], 10) - q(exp, 10)) <= D(tol):
                total += weights.get(name, 0)
        return total
    return score


def mutate(values: dict[str, str], name: str, delta: Decimal) -> dict[str, str]:
    v = dict(values)
    v[name] = str(q(D(str(values[name])) + delta, 10))
    return v


@dataclass
class MutationResult:
    name: str
    baseline: int
    outside_tolerance: int
    inside_tolerance: int
    outside_flips: bool
    inside_holds: bool
    passed: bool
    inside_na: bool = False


def run(expected: dict[str, tuple[str, str]], weights: dict[str, int],
        max_weight: int = 100) -> list[MutationResult]:
    scorer = tolerance_scorer(expected, weights)
    base_vals = {k: v[0] for k, v in expected.items()}
    base = scorer(base_vals)
    out: list[MutationResult] = []
    for name, (exp, tol) in expected.items():
        t = D(tol)
        step = t * D("2") if t > 0 else D("0.01")
        out_val = scorer(mutate(base_vals, name, step))
        if t == 0:
            # 容差为 0：任何改动都必须翻分，"容差内不动"不适用
            out.append(MutationResult(name, base, out_val, out_val,
                                      outside_flips=out_val < base, inside_holds=True,
                                      passed=(out_val < base), inside_na=True))
            continue
        in_val = scorer(mutate(base_vals, name, step * D("0.25")))
        out.append(MutationResult(
            name, base, out_val, in_val,
            outside_flips=out_val < base,
            inside_holds=in_val == base,
            passed=(out_val < base) and (in_val == base)))
    return out


def summarise(results: list[MutationResult]) -> dict:
    bad = [r for r in results if not r.passed]
    return {"total": len(results), "failed": len(bad),
            "ok": not bad,
            "failed_items": [{"name": r.name, "baseline": r.baseline,
                              "outside": r.outside_tolerance, "inside": r.inside_tolerance}
                             for r in bad]}
