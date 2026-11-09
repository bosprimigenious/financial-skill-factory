"""TCA 样板：逐笔交易成本测算 + 可执行的判分器 + 反例矩阵。

为什么把判分器写成代码：改造方案要求"用可复算的金融规则检查交付"，
而不是检查文件是否存在。判分器必须能被反例打穿——打不穿就是装饰。

口径（写死在代码里，题面不复述）：
  滑点      buy: 成交价 - 到达价；sell: 到达价 - 成交价   （正数=不利）
  显性费用  佣金(分档+最低收费) + 过户费(双边) + 经手费(双边) + 印花税(仅卖出)
  Cost BPS  10000 × (Σ滑点金额 + Σ显性费用) / Σ到达价×成交数量
  未成交     单独列示，不计入 Cost BPS；机会成本不在本任务口径内
"""
from __future__ import annotations

from decimal import Decimal as D

from financial_verifiers.core import q

BPS = D("10000")


def _num(x) -> D:
    return D(str(x).strip().replace(",", ""))


def commission(amount: D, tiers: list[tuple[str, str]], min_fee: D) -> D:
    rate = _num(tiers[0][1])
    for floor, r in tiers:
        if amount >= _num(floor):
            rate = _num(r)
    return max(q(amount * rate, 2), min_fee)


def compute(fills: list[dict], fees: dict[str, dict],
            unfilled_orders: list[dict] | None = None) -> dict:
    """返回逐笔、订单级与总额；全部 Decimal。

    unfilled_orders：完全没有成交的订单（必须单列未成交，不能被静默丢弃）。
    """
    rows, by_order = [], {}
    tot_slip = tot_fee = tot_notional = D("0")
    notional_base = D("0")
    for f in fills:
        side = f["side"].upper()
        if side not in ("BUY", "SELL"):
            raise ValueError(f"未知方向 {side}")
        price, arrival, qty = _num(f["fill_price"]), _num(f["arrival_price"]), _num(f["fill_qty"])
        cfg = fees[f["symbol"]]
        notional = q(price * qty, 2)
        slip_unit = (price - arrival) if side == "BUY" else (arrival - price)
        slip = q(slip_unit * qty, 2)
        comm = commission(notional, cfg["commission_tiers"], _num(cfg["min_fee"]))
        transfer = q(notional * _num(cfg["transfer_rate"]), 2)
        exchange = q(notional * _num(cfg["exchange_fee_rate"]), 2)
        stamp = q(notional * _num(cfg["stamp_duty_sell"]), 2) if side == "SELL" else D("0")
        explicit = q(comm + transfer + exchange + stamp, 2)
        rows.append({
            "fill_id": f["fill_id"], "order_id": f["order_id"], "symbol": f["symbol"],
            "side": side, "fill_qty": qty, "fill_price": price, "arrival_price": arrival,
            "notional": notional, "slippage": slip, "commission": comm,
            "transfer_fee": transfer, "exchange_fee": exchange, "stamp_duty": stamp,
            "explicit_fee": explicit, "total_cost": q(slip + explicit, 2),
            "cost_bps": q((slip + explicit) / notional * BPS, 4) if notional else D("0"),
        })
        o = by_order.setdefault(f["order_id"], {
            "order_id": f["order_id"], "symbol": f["symbol"], "side": side,
            "fill_qty": D("0"), "order_qty": _num(f["order_qty"]),
            "arrival_price": arrival, "notional": D("0"), "slippage": D("0"),
            "explicit_fee": D("0"), "total_cost": D("0"),
        })
        for k in ("fill_qty", "notional", "slippage", "explicit_fee", "total_cost"):
            o[k] += rows[-1][{"fill_qty": "fill_qty", "notional": "notional",
                              "slippage": "slippage", "explicit_fee": "explicit_fee",
                              "total_cost": "total_cost"}[k]]
        tot_slip += slip
        tot_fee += explicit
        tot_notional += notional
        notional_base += q(arrival * qty, 2)

    for u in (unfilled_orders or []):
        by_order[u["order_id"]] = {
            "order_id": u["order_id"], "symbol": u["symbol"], "side": u["side"].upper(),
            "fill_qty": D("0"), "order_qty": _num(u["order_qty"]),
            "arrival_price": _num(u["arrival_price"]), "notional": D("0"),
            "slippage": D("0"), "explicit_fee": D("0"), "total_cost": D("0"),
        }

    orders = []
    for o in by_order.values():
        o["unfilled_qty"] = o["order_qty"] - o["fill_qty"]
        o["cost_bps"] = q(o["total_cost"] / o["notional"] * BPS, 4) if o["notional"] else D("0")
        orders.append(o)
    orders.sort(key=lambda x: x["order_id"])

    return {
        "fills": rows,
        "orders": orders,
        "summary": {
            "fill_count": len(rows),
            "notional": q(tot_notional, 2),
            "slippage": q(tot_slip, 2),
            "explicit_fee": q(tot_fee, 2),
            "total_cost": q(tot_slip + tot_fee, 2),
            "cost_bps": q((tot_slip + tot_fee) / notional_base * BPS, 4) if notional_base else D("0"),
            "unfilled_qty": sum((o["unfilled_qty"] for o in orders), D("0")),
        },
    }


# ---------------- 判分（考点即代码） ----------------
def grade(result: dict, submission: dict) -> dict:
    """按 8 条考点判分。submission 是被测方的交付结构；result 是 GT。"""
    items = []

    def add(cid, weight, ok, detail=""):
        items.append({"id": cid, "weight": weight, "passed": bool(ok), "detail": detail})

    s, gs = (submission.get("summary") or {}), result["summary"]
    add("R1", 14, submission.get("fills") is not None, "缺逐笔底稿")
    # R2 滑点方向与金额
    slip_ok = all(
        abs(_num(a["slippage"]) - _num(b["slippage"])) <= D("0.01")
        for a, b in zip((submission.get("fills") or []), result["fills"])) and \
        len((submission.get("fills") or [])) == len(result["fills"])
    add("R2", 16, slip_ok, "滑点方向或金额错")
    # R3 佣金分档与最低收费
    comm_ok = all(abs(_num(a["commission"]) - _num(b["commission"])) <= D("0.01")
                  for a, b in zip((submission.get("fills") or []), result["fills"]))
    add("R3", 14, comm_ok, "佣金分档或最低收费错")
    # R4 印花税仅卖出
    stamp_ok = all(abs(_num(a["stamp_duty"]) - _num(b["stamp_duty"])) <= D("0.01")
                   for a, b in zip((submission.get("fills") or []), result["fills"]))
    add("R4", 10, stamp_ok, "印花税方向错")
    # R5 订单级汇总（加权，不是简单平均）
    ord_ok = all(any(o["order_id"] == x["order_id"] and abs(_num(o["cost_bps"]) - _num(x["cost_bps"])) <= D("0.0001")
                     for x in result["orders"]) for o in (submission.get("orders") or [])) and \
        len((submission.get("orders") or [])) == len(result["orders"])
    add("R5", 16, ord_ok, "订单级汇总缺失或非加权")
    # R6 未成交单列且不计入成本
    add("R6", 10, abs(_num(s.get("unfilled_qty", "0")) - _num(gs["unfilled_qty"])) <= D("0.0001"),
        "未成交数量错或未单列")
    # R7 总额与 Cost BPS
    add("R7", 12, abs(_num(s.get("total_cost", "0")) - _num(gs["total_cost"])) <= D("0.05")
        and abs(_num(s.get("cost_bps", "0")) - _num(gs["cost_bps"])) <= D("0.01"),
        "总成本或 Cost BPS 错")
    # R8 口径声明：不得把未成交机会成本混入
    add("R8", 8, submission.get("scope_note", "").strip() != "", "缺口径声明")

    score = sum(i["weight"] for i in items if i["passed"])
    return {"items": items, "score": score, "total": 100,
            "failed": [i["id"] for i in items if not i["passed"]]}
