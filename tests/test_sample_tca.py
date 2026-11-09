"""TCA 样板的反例矩阵。

要求：每条考点都必须能被一个可构造的错误交付打穿；
打不穿的考点是装饰，不算验收能力。
"""
import copy
import importlib.util
import json
import unittest
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "samples" / "tca-01"
spec = importlib.util.spec_from_file_location("tca", HERE / "tca.py")
tca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tca)


def build():
    import csv
    fills, fees, unfilled = [], {}, []
    with (HERE / "materials/01_成交回报.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            fills.append(r)
    tiers = {}
    with (HERE / "materials/02_费率与基准.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            c = tiers.setdefault(r["symbol"], {
                "commission_tiers": [], "min_fee": r["min_fee"],
                "transfer_rate": r["transfer_rate"],
                "exchange_fee_rate": r["exchange_fee_rate"],
                "stamp_duty_sell": r["stamp_duty_sell"]})
            c["commission_tiers"].append([r["tier_floor"], r["tier_rate"]])
    with (HERE / "materials/03_未成交订单.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            unfilled.append(r)
    return tca.compute(fills, tiers, unfilled)


GT = build()


def submission_from_gt(gt):
    return {"fills": copy.deepcopy(gt["fills"]), "orders": copy.deepcopy(gt["orders"]),
            "summary": copy.deepcopy(gt["summary"]), "scope_note": "不含未成交机会成本"}


def score(sub):
    return tca.grade(GT, sub)


class TestBaseline(unittest.TestCase):
    def test_gt_scores_full_marks(self):
        r = score(submission_from_gt(GT))
        self.assertEqual(r["score"], 100)
        self.assertEqual(r["failed"], [])

    def test_totals_are_consistent(self):
        s = GT["summary"]
        self.assertEqual(s["total_cost"], s["slippage"] + s["explicit_fee"])
        self.assertEqual(s["fill_count"], 5)
        self.assertEqual(s["unfilled_qty"], D("5100"))   # O1 0 + O2 0 + O3 5000 + O4 100


class TestCounterExamples(unittest.TestCase):
    """每个用例只注入一类专业错误，断言命中的考点就是预期那一条。"""

    def assert_caught(self, sub, expected_item):
        r = score(sub)
        self.assertIn(expected_item, r["failed"], f"未命中 {expected_item}：failed={r['failed']}")
        self.assertLess(r["score"], 100)

    def test_C1_slippage_direction_flipped_on_sell(self):
        sub = submission_from_gt(GT)
        for row in sub["fills"]:
            if row["side"] == "SELL":
                row["slippage"] = -row["slippage"]
        self.assert_caught(sub, "R2")

    def test_C2_wrong_benchmark_used(self):
        sub = submission_from_gt(GT)
        sub["fills"][0]["slippage"] = D(sub["fills"][0]["slippage"]) + D("100")
        self.assert_caught(sub, "R2")

    def test_C3_commission_without_minimum(self):
        sub = submission_from_gt(GT)
        for row in sub["fills"]:
            row["commission"] = (D(str(row["commission"])) - D("5")).quantize(D("0.01")) \
                if D(str(row["commission"])) <= D("100") else row["commission"]
        self.assert_caught(sub, "R3")

    def test_C4_stamp_duty_charged_on_buy(self):
        sub = submission_from_gt(GT)
        for row in sub["fills"]:
            if row["side"] == "BUY":
                row["stamp_duty"] = (D(str(row["notional"])) * D("0.0005")).quantize(D("0.01"))
        self.assert_caught(sub, "R4")

    def test_C5_order_bps_uses_simple_average(self):
        sub = submission_from_gt(GT)
        for o in sub["orders"]:
            fills = [f for f in sub["fills"] if f["order_id"] == o["order_id"]]
            if fills:
                o["cost_bps"] = (sum(D(str(f["cost_bps"])) for f in fills) / len(fills)
                                 ).quantize(D("0.0001"))
        self.assert_caught(sub, "R5")

    def test_C6_unfilled_dropped(self):
        sub = submission_from_gt(GT)
        sub["summary"]["unfilled_qty"] = D("0")
        self.assert_caught(sub, "R6")

    def test_C7_cost_bps_uses_share_quantity_denominator(self):
        sub = submission_from_gt(GT)
        qty = sum(D(str(f["fill_qty"])) for f in sub["fills"])
        sub["summary"]["cost_bps"] = (
            (D(str(sub["summary"]["total_cost"])) / qty) * D("10000")).quantize(D("0.0001"))
        self.assert_caught(sub, "R7")

    def test_C8_missing_scope_note(self):
        sub = submission_from_gt(GT)
        sub["scope_note"] = "  "
        self.assert_caught(sub, "R8")

    def test_C9_fills_omitted(self):
        sub = submission_from_gt(GT)
        sub["fills"] = None
        self.assert_caught(sub, "R1")


class TestCoverage(unittest.TestCase):
    def test_every_rubric_item_is_reachable(self):
        """8 条考点都必须至少被打穿一次，否则该考点不构成验收能力。"""
        cases = {
            "R1": lambda s: s.update(fills=None),
            "R2": lambda s: s["fills"][0].update(slippage=D("999")),
            "R3": lambda s: s["fills"][0].update(commission=D("0.01")),
            "R4": lambda s: s["fills"][0].update(stamp_duty=D("1")),
            "R5": lambda s: s["orders"][0].update(cost_bps=D("999")),
            "R6": lambda s: s["summary"].update(unfilled_qty=D("0")),
            "R7": lambda s: s["summary"].update(cost_bps=D("999")),
            "R8": lambda s: s.update(scope_note=""),
        }
        caught = set()
        for item, mutate in cases.items():
            sub = submission_from_gt(GT)
            mutate(sub)
            caught.add(item) if item in score(sub)["failed"] else None
        self.assertEqual(caught, set(cases), f"未被覆盖的考点：{set(cases) - caught}")

    def test_weights_sum_to_100(self):
        r = score(submission_from_gt(GT))
        self.assertEqual(sum(i["weight"] for i in r["items"]), 100)


if __name__ == "__main__":
    unittest.main()
