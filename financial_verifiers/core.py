"""Stage 4 · 确定性计算基座。

原则：数值由 Decimal 计算，不由 LLM 生成。每个校验器返回 `Check` 列表，
每条带期望值、实际值、容差、证据锚点。LLM 只负责解释与形成意见。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

D = Decimal


def q(x, places: int = 2) -> Decimal:
    """四舍五入（金融惯例 ROUND_HALF_UP），不用 Python 默认的银行家舍入。"""
    exp = Decimal(1).scaleb(-places)
    return D(x).quantize(exp, rounding=ROUND_HALF_UP)


def num(x) -> Decimal:
    try:
        return D(str(x).strip().replace(",", "").replace("%", ""))
    except (InvalidOperation, AttributeError) as e:
        raise ValueError(f"无法解析为数值：{x!r}") from e


@dataclass(frozen=True)
class Check:
    name: str
    expected: Decimal | str
    actual: Decimal | str
    tolerance: Decimal = D("0")
    passed: bool = True
    anchor: str = ""            # 证据锚点：文件#字段/行
    note: str = ""

    @staticmethod
    def make(name: str, expected, actual, tol="0.01", anchor="") -> "Check":
        e, a, t = num(expected), num(actual), num(tol)
        ok = abs(e - a) <= t
        return Check(name, e, a, t, ok, anchor)

    def __str__(self) -> str:
        flag = "PASS" if self.passed else "FAIL"
        return f"[{flag}] {self.name}: 期望 {self.expected} 实得 {self.actual} 容差 {self.tolerance} {self.anchor}"


@dataclass
class VerifierResult:
    verifier: str
    checks: list[Check] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.passed]


REGISTRY: dict[str, callable] = {}


def register(name: str):
    def deco(fn):
        REGISTRY[name] = fn
        return fn
    return deco


def run(name: str, params: dict) -> VerifierResult:
    if name not in REGISTRY:
        raise KeyError(f"未注册的验证器 {name}；已注册 {sorted(REGISTRY)}")
    return REGISTRY[name](params)
