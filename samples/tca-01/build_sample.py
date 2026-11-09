#!/usr/bin/env python3
"""生成 TCA 样板的材料与标准答案（单一事实源）。

材料性质：**回归夹具（合成）**，不是真实委托材料。字段契约见 README，
换成真实授权材料时只替换 materials/*.csv，本脚本不需要改（断言会重算）。

用法：PYTHONPATH=. python samples/tca-01/build_sample.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
MAT = HERE / "materials"
GT = HERE / "gt"

FEES = {
    "600519": {"commission_tiers": [["0", "0.00025"], ["1000000", "0.0002"]],
               "min_fee": "5", "transfer_rate": "0.00001",
               "exchange_fee_rate": "0.0000487", "stamp_duty_sell": "0.0005"},
    "000001": {"commission_tiers": [["0", "0.0003"], ["500000", "0.00025"]],
               "min_fee": "5", "transfer_rate": "0.00001",
               "exchange_fee_rate": "0.0000487", "stamp_duty_sell": "0.0005"},
}

FILLS = [
    {"fill_id": "F001", "order_id": "O1", "symbol": "600519", "side": "BUY",
     "fill_time": "2026-10-15T09:31:02", "fill_price": "1501.20", "fill_qty": "200",
     "order_qty": "300", "arrival_price": "1500.00"},
    {"fill_id": "F002", "order_id": "O1", "symbol": "600519", "side": "BUY",
     "fill_time": "2026-10-15T09:31:47", "fill_price": "1499.80", "fill_qty": "100",
     "order_qty": "300", "arrival_price": "1500.00"},
    {"fill_id": "F003", "order_id": "O2", "symbol": "000001", "side": "SELL",
     "fill_time": "2026-10-15T10:02:11", "fill_price": "11.18", "fill_qty": "12000",
     "order_qty": "20000", "arrival_price": "11.20"},
    {"fill_id": "F004", "order_id": "O2", "symbol": "000001", "side": "SELL",
     "fill_time": "2026-10-15T10:02:55", "fill_price": "11.24", "fill_qty": "8000",
     "order_qty": "20000", "arrival_price": "11.20"},
    {"fill_id": "F005", "order_id": "O3", "symbol": "000001", "side": "BUY",
     "fill_time": "2026-10-15T10:15:30", "fill_price": "11.16", "fill_qty": "3000",
     "order_qty": "8000", "arrival_price": "11.15"},
]
UNFILLED = [{"order_id": "O4", "symbol": "600519", "side": "SELL",
             "order_qty": "100", "arrival_price": "1512.00"}]


def main() -> int:
    import importlib.util
    spec = importlib.util.spec_from_file_location("tca", HERE / "tca.py")
    tca = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tca)  # type: ignore[union-attr]

    MAT.mkdir(parents=True, exist_ok=True)
    GT.mkdir(parents=True, exist_ok=True)

    def w(path, header, rows):
        with open(path, "w", newline="", encoding="utf-8") as f:
            cw = csv.writer(f)
            cw.writerow(header)
            cw.writerows(rows)

    w(MAT / "01_成交回报.csv",
      ["fill_id", "order_id", "symbol", "side", "fill_time", "fill_price", "fill_qty",
       "order_qty", "arrival_price"],
      [[f["fill_id"], f["order_id"], f["symbol"], f["side"], f["fill_time"],
        f["fill_price"], f["fill_qty"], f["order_qty"], f["arrival_price"]] for f in FILLS])
    w(MAT / "02_费率与基准.csv",
      ["symbol", "tier_floor", "tier_rate", "min_fee", "transfer_rate",
       "exchange_fee_rate", "stamp_duty_sell"],
      [[s, t[0], t[1], c["min_fee"], c["transfer_rate"], c["exchange_fee_rate"],
        c["stamp_duty_sell"]] for s, c in FEES.items() for t in c["commission_tiers"]])
    w(MAT / "03_未成交订单.csv", ["order_id", "symbol", "side", "order_qty", "arrival_price"],
      [[u["order_id"], u["symbol"], u["side"], u["order_qty"], u["arrival_price"]] for u in UNFILLED])

    gt = tca.compute(FILLS, FEES, UNFILLED)

    def fmt(x):
        return f"{x}"

    w(GT / "逐笔成本底稿.csv",
      ["fill_id", "order_id", "symbol", "side", "fill_qty", "fill_price", "arrival_price",
       "notional", "slippage", "commission", "transfer_fee", "exchange_fee", "stamp_duty",
       "explicit_fee", "total_cost", "cost_bps"],
      [[r["fill_id"], r["order_id"], r["symbol"], r["side"], fmt(r["fill_qty"]),
        fmt(r["fill_price"]), fmt(r["arrival_price"]), fmt(r["notional"]), fmt(r["slippage"]),
        fmt(r["commission"]), fmt(r["transfer_fee"]), fmt(r["exchange_fee"]),
        fmt(r["stamp_duty"]), fmt(r["explicit_fee"]), fmt(r["total_cost"]),
        fmt(r["cost_bps"])] for r in gt["fills"]])
    w(GT / "订单级汇总.csv",
      ["order_id", "symbol", "side", "order_qty", "fill_qty", "unfilled_qty",
       "notional", "slippage", "explicit_fee", "total_cost", "cost_bps"],
      [[o["order_id"], o["symbol"], o["side"], fmt(o["order_qty"]), fmt(o["fill_qty"]),
        fmt(o["unfilled_qty"]), fmt(o["notional"]), fmt(o["slippage"]),
        fmt(o["explicit_fee"]), fmt(o["total_cost"]), fmt(o["cost_bps"])]
       for o in gt["orders"]])
    (GT / "summary.json").write_text(
        json.dumps({k: str(v) for k, v in gt["summary"].items()}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    # 自校验：GT 必须能被判分器判满分（否则判分器与计算不一致）
    res = tca.grade(gt, {"fills": gt["fills"], "orders": gt["orders"],
                         "summary": gt["summary"], "scope_note": "不含未成交机会成本"})
    print("GT 自检：", res["score"], "/100", "failed=", res["failed"])
    s = gt["summary"]
    print(f"逐笔 {s['fill_count']} 笔  名义 {s['notional']}  滑点 {s['slippage']}  "
          f"费用 {s['explicit_fee']}  合计 {s['total_cost']}  Cost {s['cost_bps']} bps  "
          f"未成交 {s['unfilled_qty']}")
    return 0 if res["score"] == 100 else 1


if __name__ == "__main__":
    raise SystemExit(main())
