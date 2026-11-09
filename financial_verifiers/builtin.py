"""五个金融验证器（确定性，Decimal 精确）。

对应改造建议里的第一批回归案例类型：
  capital           —— 净资本折算（招商证券类）
  reconciliation    —— 报表勾稽（财务报告复核类）
  fund_nav          —— 基金净值与份额（基金运营类）
  transaction_cost  —— 交易费用分档（经纪执行类）
  portfolio         —— 组合权重与情景收益（投研类）
"""
from __future__ import annotations

from .core import D, Check, VerifierResult, q, register


def _res(name: str, checks: list[Check]) -> VerifierResult:
    return VerifierResult(name, checks)


@register("capital")
def capital(p: dict) -> VerifierResult:
    """净资本 = 净资产 − 各项扣减；次级债按剩余期限分档计入，且不超净资产 50%。

    p = {"net_assets": "5000", "sub_debt": [{"amount":"1000","remaining_years":3.2},...],
         "deductions": [{"name":"商誉","amount":"120"}],
         "expected": {"net_capital": "...", "qualified_sub_debt": "..."}}
    """
    na = q(p["net_assets"], 4)
    qual, rows = D("0"), []
    for b in p.get("sub_debt", []):
        amt, yrs = q(b["amount"], 4), float(b["remaining_years"])
        # 分档：>=5 年 100%；4-5 年 90%；3-4 年 70%；2-3 年 50%；1-2 年 30%；<1 年 0%
        rate = (1.00 if yrs >= 5 else 0.90 if yrs >= 4 else 0.70 if yrs >= 3
                else 0.50 if yrs >= 2 else 0.30 if yrs >= 1 else 0.00)
        qual += q(amt * D(str(rate)), 4)
        rows.append((b.get("name", "次级债"), amt, yrs, rate))
    cap = q(na * D("0.5"), 4)
    qual = min(qual, cap)
    ded = sum((q(x["amount"], 4) for x in p.get("deductions", [])), D("0"))
    nc = q(na - ded + qual, 4)
    checks = [Check.make("次级债按期限折算后合计", p.get("expected", {}).get("qualified_sub_debt", qual), qual,
                         tol="0.01", anchor="次级债明细#剩余期限"),
              Check.make("净资本", p["expected"]["net_capital"], nc, tol="0.01",
                         anchor="净资产−扣减+合格次级债")]
    return _res("capital", checks)


@register("reconciliation")
def reconciliation(p: dict) -> VerifierResult:
    """明细合计与表头/总额勾稽；资产负债表恒等式。

    p = {"header": "1250.00", "details": ["600.00","650.00"], "tol": "0.01"}
    或 {"assets":"...","liabilities":"...","equity":"..."}
    """
    checks: list[Check] = []
    if "header" in p:
        tot = sum((q(x, 4) for x in p["details"]), D("0"))
        checks.append(Check.make("明细合计=表头", p["header"], tot,
                                 tol=p.get("tol", "0.01"), anchor="明细行求和"))
    if {"assets", "liabilities", "equity"} <= set(p):
        rhs = q(p["liabilities"], 4) + q(p["equity"], 4)
        checks.append(Check.make("资产=负债+权益", p["assets"], rhs,
                                 tol=p.get("tol", "0.01"), anchor="资产负债表恒等式"))
    if not checks:
        raise ValueError("reconciliation 需要 header/details 或 assets/liabilities/equity")
    return _res("reconciliation", checks)


@register("fund_nav")
def fund_nav(p: dict) -> VerifierResult:
    """单位净值 = (资产 − 负债) / 份额；并核对管理费计提 = 前一日净值 × 费率 / 365 × 天数。

    p = {"assets":"...","liabilities":"...","shares":"...","fee":{"nav_prev":"1.2","rate":"0.015","days":31},
         "expected":{"nav":"...","fee":"..."}}
    """
    assets, liab = q(p["assets"], 4), q(p["liabilities"], 4)
    shares = q(p["shares"], 4)
    if shares <= 0:
        raise ValueError("份额必须为正")
    nav = q((assets - liab) / shares, 6)
    checks = [Check.make("单位净值", p.get("expected", {}).get("nav", nav), nav,
                         tol=p.get("tol", "0.000001"), anchor="(资产−负债)/份额")]
    if "fee" in p:
        f = p["fee"]
        fee = q(q(f["nav_prev"], 6) * q(f["rate"], 6) * D(str(f["days"]))
                    / D("365") * shares, 2)
        checks.append(Check.make("管理费计提", p["expected"]["fee"], fee, tol="0.01",
                                 anchor="前一日净值×费率/365×天数"))
    return _res("fund_nav", checks)


@register("transaction_cost")
def transaction_cost(p: dict) -> VerifierResult:
    """佣金按成交额分档费率 + 最低收费；另加过户费与经手费。

    p = {"trades": [{"amount":"120000","side":"buy"}], "tiers": [[0,0.0025],[1000000,0.002]],
         "min_fee":"5", "transfer_rate":"0.00001", "exchange_rate":"0.0000487",
         "expected_total":"..."}
    """
    tiers = [(D(str(t[0])), D(str(t[1]))) for t in p["tiers"]]
    tiers.sort()
    min_fee = D(str(p.get("min_fee", "5")))
    tr, ex = D(str(p.get("transfer_rate", "0"))), D(str(p.get("exchange_rate", "0")))
    total, checks = D("0"), []
    for i, t in enumerate(p["trades"], 1):
        amt = q(t["amount"], 2)
        rate = tiers[0][1]
        for floor, r in tiers:
            if amt >= floor:
                rate = r
        comm = max(q(amt * rate, 2), min_fee)
        cost = comm + q(amt * tr, 2) + q(amt * ex, 2)
        total += cost
        checks.append(Check.make(f"第{i}笔总费用", q(amt * rate, 2) if amt * rate > min_fee else min_fee,
                                 comm, tol="0.01", anchor=f"成交额{amt}#分档费率{rate}"))
    total = q(total, 2)
    checks.append(Check.make("费用合计", p["expected_total"], total, tol="0.02", anchor="逐笔汇总"))
    return _res("transaction_cost", checks)


@register("portfolio")
def portfolio(p: dict) -> VerifierResult:
    """权重合计=1；加权收益 = Σ w×r；检查单票超限。

    p = {"holdings":[{"name":"A","value":"600","ret":"0.05"},...],
         "max_weight":"0.4", "expected":{"return":"..."}}
    """
    hv = [(h["name"], q(h["value"], 4), D(str(h["ret"]))) for h in p["holdings"]]
    total = sum((v for _, v, _ in hv), D("0"))
    if total <= 0:
        raise ValueError("组合市值必须为正")
    checks = [Check.make("权重合计", "1", q(sum((v / total for _, v, _ in hv), D("0")), 8),
                         tol="0.000001", anchor="各持仓市值/合计")]
    ret = q(sum(((v / total) * r for _, v, r in hv), D("0")), 8)
    checks.append(Check.make("组合加权收益", p["expected"]["return"], ret, tol="0.000001",
                             anchor="Σ 权重×收益率"))
    if "max_weight" in p:
        worst = max(hv, key=lambda x: x[1] / total)
        checks.append(Check.make(f"最大单票权重（{worst[0]}）不超限", p["max_weight"],
                                 q(worst[1] / total, 6), tol="0.000001", anchor="单票权重上限"))
    return _res("portfolio", checks)
