"""两个新增金融验证器：执行偏差分解（Implementation Shortfall）与 Carry 瀑布。

都属于"公式明确、口径必须写清、模型容易编数"的类型：
  - IS 分解：延迟 / 冲击 / 未成交机会成本，三项必须可加总
  - Carry 瀑布：返还本金 → 优先回报 → 追补 → 二八分成，总额必须守恒

全部 Decimal；每个口径都在参数里显式声明，不给"行业默认值"。
"""
from __future__ import annotations

from .core import D, Check, VerifierResult, q, register

EPS = D("0.0001")


@register("implementation_shortfall")
def implementation_shortfall(p: dict) -> VerifierResult:
    """执行偏差分解（单位：bps，统一以决策价为分母，保证三项可加总）。

    p = {
      "side": "BUY"|"SELL",
      "decision_price": "10.00", "arrival_price": "10.05",
      "exec_price": "10.12", "final_price": "10.20",
      "order_qty": "100000", "filled_qty": "80000",
      "expected_total_bps": "..."   # 可选，交叉核对
    }

    口径（写死）：
      sign = +1 (BUY) / -1 (SELL)，正数一律表示对投资者不利
      delay       = sign*(arrival-decision)/decision*1e4 * w
      impact      = sign*(exec-arrival)/decision*1e4 * w
      opportunity = sign*(final-arrival)/decision*1e4 * (1-w)
      total       = delay + impact + opportunity     w = filled/order
    """
    side = p["side"].upper()
    if side not in ("BUY", "SELL"):
        raise ValueError("side 必须是 BUY 或 SELL")
    sign = D("1") if side == "BUY" else D("-1")
    pd, pa = q(p["decision_price"], 6), q(p["arrival_price"], 6)
    pe, pf = q(p["exec_price"], 6), q(p["final_price"], 6)
    oq, fq = q(p["order_qty"], 6), q(p["filled_qty"], 6)
    if oq <= 0 or fq < 0 or fq > oq:
        raise ValueError("数量非法：要求 0 <= filled_qty <= order_qty 且 order_qty > 0")
    w = fq / oq
    k = D("10000") / pd

    delay = q(sign * (pa - pd) * k * w, 4)
    impact = q(sign * (pe - pa) * k * w, 4)
    opp = q(sign * (pf - pa) * k * (D("1") - w), 4)
    total = q(delay + impact + opp, 4)

    checks = [
        Check.make("延迟成本(bps)", delay, delay, tol="0.0001", anchor="决策价→到达价"),
        Check.make("冲击成本(bps)", impact, impact, tol="0.0001", anchor="到达价→成交价"),
        Check.make("机会成本(bps)", opp, opp, tol="0.0001", anchor="到达价→截止价×未成交比例"),
        Check.make("三项加总=总执行偏差", total, q(delay + impact + opp, 4), tol="0.0001",
                   anchor="可加总性"),
    ]
    if "expected_total_bps" in p:
        checks.append(Check.make("总偏差与期望一致", p["expected_total_bps"], total,
                                 tol=p.get("tol", "0.01"), anchor="冻结考点"))
    # 全额成交时机会成本必须为 0
    if fq == oq:
        checks.append(Check.make("全额成交时机会成本为0", "0", opp, tol="0.0001", anchor="口径自检"))
    return VerifierResult("implementation_shortfall", checks)


@register("carry_waterfall")
def carry_waterfall(p: dict) -> VerifierResult:
    """欧式（基金整体）瀑布：返还本金(按出资比例) → 优先回报 → 追补 → 二八分成。

    p = {"lp_commit","gp_commit","distributable","preferred_return_pct",
         "catch_up_ratio","carry_rate","clawback"}

    口径（写死，不给默认值）：
      1) 本金按出资比例返还（不做 LP 先行）
      2) 优先回报 = LP 出资 × preferred_return_pct，先于任何业绩报酬
      3) 追补：GP 取 carry/(1-carry) × 优先回报 后，GP 累计业绩报酬恰为 carry × 总利润；
         catch_up_ratio 为 GP 在追补池中的占比（<1 即追补不足）
      4) 剩余按 carry_rate 分配给 GP，其余给 LP
      5) clawback：GP 业绩报酬上限 = carry_rate × 利润
    """
    lp_c, gp_c = q(p["lp_commit"], 2), q(p["gp_commit"], 2)
    cap = q(lp_c + gp_c, 2)
    dist = q(p["distributable"], 2)
    if dist < 0 or cap <= 0:
        raise ValueError("可分配金额不能为负，出资合计必须为正")
    pref_rate = q(p["preferred_return_pct"], 6)
    catch = q(p["catch_up_ratio"], 6)
    carry = q(p["carry_rate"], 6)
    if not (0 <= pref_rate < 1 and 0 <= carry < 1 and 0 < catch):
        raise ValueError("参数越界：preferred_return_pct/carry_rate ∈ [0,1)，catch_up_ratio > 0")

    profit = q(max(dist - cap, D("0")), 2)
    lp_ret = q(dist * lp_c / cap, 2) if dist < cap else lp_c
    gp_ret = q(min(dist, cap) - lp_ret, 2) if dist < cap else gp_c
    remaining = q(dist - lp_ret - gp_ret, 2)

    lp_pref = min(remaining, q(lp_c * pref_rate, 2))
    remaining = q(remaining - lp_pref, 2)

    gp_carry = D("0")
    lp_split = D("0")
    target_carry = q(profit * carry, 2)
    if remaining > 0 and profit > 0 and carry > 0:
        ideal_catch = q(lp_pref * carry / (D("1") - carry), 2)
        pool = q(ideal_catch / catch, 2) if catch > 0 else ideal_catch
        pool = min(pool, remaining)
        gp_carry = q(min(q(pool * catch, 2), remaining), 2)
        remaining = q(remaining - pool, 2)
        gp_carry = q(gp_carry + q(remaining * carry, 2), 2)
        lp_split = q(remaining - q(remaining * carry, 2), 2)
        remaining = D("0")
    else:
        lp_split = remaining
        remaining = D("0")

    if p.get("clawback", True):
        gp_carry = q(min(gp_carry, target_carry), 2)

    lp_total = q(lp_ret + lp_pref + lp_split, 2)
    gp_total = q(gp_ret + gp_carry, 2)
    # 守恒：若因 clawback 削减了 GP，削减额回到 LP
    shortfall = q(dist - lp_total - gp_total, 2)
    if shortfall != 0:
        lp_total = q(lp_total + shortfall, 2)

    checks = [
        Check.make("分配总额=可分配额", dist, q(lp_total + gp_total, 2), tol="0.01", anchor="金额守恒"),
        Check.make("本金合计=出资合计", cap, q(lp_c + gp_c, 2), tol="0.01", anchor="出资表"),
        Check("GP业绩报酬不超上限", target_carry, q(max(gp_total - gp_ret, D("0")), 2),
              tolerance=D("0.01"),
              passed=q(max(gp_total - gp_ret, D("0")), 2) <= target_carry + D("0.01"),
              anchor="carry_rate×利润（上限，不要求等于）"),
    ]
    if "expected_gp_total" in p:
        checks.append(Check.make("GP 合计与期望一致", p["expected_gp_total"], gp_total,
                                 tol="0.01", anchor="冻结考点"))
    if "expected_lp_total" in p:
        checks.append(Check.make("LP 合计与期望一致", p["expected_lp_total"], lp_total,
                                 tol="0.01", anchor="冻结考点"))
    if "expected_carry_share" in p:
        ratio = q((gp_total - gp_ret) / profit, 6) if profit else D("0")
        checks.append(Check.make("GP 占利润比例", p["expected_carry_share"], ratio,
                                 tol="0.0001", anchor="carry 比例自检"))
    return VerifierResult("carry_waterfall", checks)
