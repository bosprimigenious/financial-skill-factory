"""新增验证器测试：执行偏差分解 + Carry 瀑布 + 一条命令跑产线。"""
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from financial_verifiers import advanced  # noqa: E402,F401  (注册)
from financial_verifiers.core import run  # noqa: E402

IS = {"side": "BUY", "decision_price": "10.00", "arrival_price": "10.05",
      "exec_price": "10.12", "final_price": "10.20",
      "order_qty": "100000", "filled_qty": "80000"}
CARRY = {"lp_commit": "80000000", "gp_commit": "20000000", "distributable": "120000000",
         "preferred_return_pct": "0.08", "catch_up_ratio": "1.0", "carry_rate": "0.20"}


class TestImplementationShortfall(unittest.TestCase):
    def test_three_components_add_up(self):
        r = run("implementation_shortfall", IS)
        self.assertTrue(r.passed)
        vals = {c.name: c.actual for c in r.checks}
        delay = vals["延迟成本(bps)"]
        impact = vals["冲击成本(bps)"]
        opp = vals["机会成本(bps)"]
        self.assertEqual(delay + impact + opp, vals["三项加总=总执行偏差"])
        self.assertGreater(delay, 0)
        self.assertGreater(impact, 0)
        self.assertGreater(opp, 0)

    def test_sell_side_direction_flips(self):
        buy = run("implementation_shortfall", IS)
        sell = run("implementation_shortfall", {**IS, "side": "SELL"})
        b = {c.name: c.actual for c in buy.checks}
        s = {c.name: c.actual for c in sell.checks}
        self.assertEqual(b["延迟成本(bps)"], -s["延迟成本(bps)"])

    def test_full_fill_has_zero_opportunity_cost(self):
        r = run("implementation_shortfall", {**IS, "filled_qty": "100000"})
        self.assertTrue(r.passed)
        self.assertEqual({c.name: c.actual for c in r.checks}["机会成本(bps)"], D("0"))

    def test_expected_total_mismatch_is_caught(self):
        r = run("implementation_shortfall", {**IS, "expected_total_bps": "100"})
        self.assertFalse(r.passed)

    def test_bad_quantity_rejected(self):
        with self.assertRaises(ValueError):
            run("implementation_shortfall", {**IS, "filled_qty": "200000"})


class TestCarryWaterfall(unittest.TestCase):
    def test_full_catch_up_reaches_exact_carry(self):
        r = run("carry_waterfall", {**CARRY, "expected_carry_share": "0.2"})
        self.assertTrue(r.passed, [str(c) for c in r.checks])
        vals = {c.name: c.actual for c in r.checks}
        self.assertEqual(vals["GP业绩报酬不超上限"], D("4000000.00"))

    def test_conservation_always_holds(self):
        for dist in ("50000000", "100000000", "100000001", "120000000", "99999999"):
            r = run("carry_waterfall", {**CARRY, "distributable": dist})
            self.assertTrue(r.passed, f"dist={dist} {[str(c) for c in r.checks]}")

    def test_loss_case_pays_no_carry(self):
        r = run("carry_waterfall", {**CARRY, "distributable": "50000000"})
        vals = {c.name: c.actual for c in r.checks}
        self.assertEqual(vals["GP业绩报酬不超上限"], D("0.00"))

    def test_insufficient_catch_up_is_below_cap_not_above(self):
        r = run("carry_waterfall", {**CARRY, "catch_up_ratio": "0.5"})
        self.assertTrue(r.passed)
        vals = {c.name: c.actual for c in r.checks}
        self.assertLess(vals["GP业绩报酬不超上限"], D("4000000.00"))

    def test_bad_params_rejected(self):
        with self.assertRaises(ValueError):
            run("carry_waterfall", {**CARRY, "carry_rate": "1.2"})


class TestPipelineCommand(unittest.TestCase):
    def test_all_runs_and_writes_report(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "state.md"
            r = subprocess.run([sys.executable, str(REPO / "tools/fsf_run.py"), "--all", "--out", str(out)],
                               capture_output=True, text=True, cwd=REPO)
            self.assertIn(r.returncode, (0, 1), r.stdout + r.stderr)
            self.assertTrue(out.is_file())
            text = out.read_text(encoding="utf-8")
            self.assertIn("产线状态", text)
            self.assertGreaterEqual(text.count("### "), 9)

    def test_missing_case_exits_2(self):
        r = subprocess.run([sys.executable, str(REPO / "tools/fsf_run.py"), "--case", "cases/nope"],
                           capture_output=True, text=True, cwd=REPO)
        self.assertEqual(r.returncode, 2)

    def test_stage_skips_are_recorded(self):
        """没有运行记录时必须写 UNTESTED/SKIP，不能默认达标。"""
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "s.md"
            subprocess.run([sys.executable, str(REPO / "tools/fsf_run.py"),
                            "--case", "cases/7689005313907642138", "--out", str(out)],
                           capture_output=True, text=True, cwd=REPO)
            text = out.read_text(encoding="utf-8")
            self.assertIn("difficulty", text)
            self.assertIn("SKIP", text)


if __name__ == "__main__":
    unittest.main()
