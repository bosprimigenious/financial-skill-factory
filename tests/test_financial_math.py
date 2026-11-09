"""V2 · 金融计算验证器测试（Decimal 精确，不用浮点近似）。"""
import unittest
from decimal import Decimal as D

from financial_verifiers import builtin  # noqa: F401  (注册验证器)
from financial_verifiers.core import q, run


class TestCapital(unittest.TestCase):
    def test_tiered_sub_debt(self):
        r = run("capital", {
            "net_assets": "5000",
            "sub_debt": [{"amount": "1000", "remaining_years": 3.2}],
            "deductions": [{"name": "商誉", "amount": "120"}],
            "expected": {"net_capital": "5580.0", "qualified_sub_debt": "700.0"},
        })
        self.assertTrue(r.passed, [str(c) for c in r.checks])
        self.assertEqual(r.checks[1].actual, D("5580.0000"))

    def test_sub_debt_capped_at_half_net_assets(self):
        r = run("capital", {
            "net_assets": "100",
            "sub_debt": [{"amount": "500", "remaining_years": 10}],
            "deductions": [],
            "expected": {"net_capital": "150", "qualified_sub_debt": "50"},
        })
        self.assertTrue(r.passed, [str(c) for c in r.checks])

    def test_under_one_year_counts_zero(self):
        r = run("capital", {
            "net_assets": "1000", "sub_debt": [{"amount": "300", "remaining_years": 0.5}],
            "deductions": [], "expected": {"net_capital": "1000", "qualified_sub_debt": "0"}})
        self.assertTrue(r.passed)

    def test_wrong_expectation_fails(self):
        r = run("capital", {
            "net_assets": "5000", "sub_debt": [{"amount": "1000", "remaining_years": 3.2}],
            "deductions": [{"name": "商誉", "amount": "120"}],
            "expected": {"net_capital": "4600", "qualified_sub_debt": "700"}})
        self.assertFalse(r.passed)


class TestFundNav(unittest.TestCase):
    def test_nav_and_fee(self):
        r = run("fund_nav", {
            "assets": "1205000", "liabilities": "5000", "shares": "1000000",
            "fee": {"nav_prev": "1.200000", "rate": "0.015", "days": 31},
            "expected": {"nav": "1.2", "fee": "1528.77"}})
        self.assertTrue(r.passed, [str(c) for c in r.checks])

    def test_round_half_up(self):
        self.assertEqual(q(D("1.005"), 2), D("1.01"))   # 银行家舍入会得 1.00


class TestTransactionCost(unittest.TestCase):
    def test_tier_and_min_fee(self):
        r = run("transaction_cost", {
            "trades": [{"amount": "120000"}, {"amount": "1000"}],
            "tiers": [[0, 0.0025], [1000000, 0.002]],
            "min_fee": "5", "transfer_rate": "0.00001", "exchange_rate": "0.0000487",
            "expected_total": "312.10"})
        self.assertTrue(r.passed, [str(c) for c in r.checks])

    def test_second_trade_hits_minimum(self):
        r = run("transaction_cost", {
            "trades": [{"amount": "1000"}], "tiers": [[0, 0.0025]],
            "min_fee": "5", "transfer_rate": "0", "exchange_rate": "0",
            "expected_total": "5"})
        self.assertTrue(r.passed)


class TestPortfolioAndReconciliation(unittest.TestCase):
    def test_portfolio_weight_and_return(self):
        r = run("portfolio", {
            "holdings": [{"name": "A", "value": "600", "ret": "0.05"},
                         {"name": "B", "value": "400", "ret": "0.10"}],
            "max_weight": "0.6", "expected": {"return": "0.07"}})
        self.assertTrue(r.passed, [str(c) for c in r.checks])

    def test_balance_sheet_identity(self):
        r = run("reconciliation", {"assets": "1250.00", "liabilities": "750.00", "equity": "500.00"})
        self.assertTrue(r.passed)

    def test_detail_sum_mismatch_detected(self):
        r = run("reconciliation", {"header": "1250.00", "details": ["600.00", "600.00"]})
        self.assertFalse(r.passed)


if __name__ == "__main__":
    unittest.main()
