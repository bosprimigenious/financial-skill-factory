"""外部八题包（Downloads 导入）的门禁测试。

这些包不是本仓库生成的，所以更要验：MANIFEST、GT 未被编造、无业务数据、两套 Rubric 分离。
"""
import json
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEST = REPO / "deliverables" / "fin8-upgraded"
CODES = ["FIN01_ALT_DATA", "FIN02_PRICE_VOLUME", "FIN03_ETF_ARB", "FIN04_PORT_ATTR",
         "FIN05_FX_SHOCK", "FIN06_CREDIT_MIGRATION", "FIN07_STRESS", "FIN08_LIQUIDITY_GAP"]


class TestImportedPackages(unittest.TestCase):
    def test_eight_packages_present(self):
        for c in CODES:
            self.assertTrue((DEST / c).is_dir(), f"缺 {c}")

    def test_25_files_each(self):
        for c in CODES:
            files = [p for p in (DEST / c).rglob("*") if p.is_file()]
            self.assertEqual(len(files), 25, f"{c}: {len(files)}")

    def test_manifest_hashes_verify(self):
        for c in CODES:
            r = subprocess.run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
                               cwd=DEST / c, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{c}: {r.stdout[-200:]}")

    def test_no_business_data(self):
        for c in CODES:
            d = DEST / c / "01_PUBLIC_DOUBAO/inputs"
            self.assertEqual(list(d.rglob("*.csv")) if d.is_dir() else [], [], f"{c} 含材料")

    def test_golden_response_not_fabricated(self):
        for c in CODES:
            t = (DEST / c / "02_PRIVATE_EXPERT/GOLDEN_RESPONSE.md").read_text(encoding="utf-8")
            self.assertIn("NOT_READY", t)
            self.assertIsNone(re.search(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b", t),
                              f"{c} 的 GT 出现成组金额，疑似编造")
            self.assertIn("Do not invent", t)

    def test_two_rubrics_separated(self):
        for c in CODES:
            p = DEST / c / "02_PRIVATE_EXPERT"
            plat = (p / "PLATFORM_RUBRIC.csv").read_text(encoding="utf-8").splitlines()[0].lower()
            intl = (p / "INTERNAL_GRADER_20x5.csv").read_text(encoding="utf-8").splitlines()[0].lower()
            self.assertIn("core_criterion", plat)
            self.assertIn("criterion_id", intl)
            self.assertNotIn("core_criterion", intl)

    def test_g7_rule_1114(self):
        for c in CODES:
            text = re.sub(r"\s+", " ", "".join(
                f.read_text(encoding="utf-8") for f in (DEST / c).rglob("*.md")))
            self.assertTrue(re.search(r"(<=|≤)\s*50", text), f"{c} 缺 Judge ≤50")
            self.assertTrue(re.search(r"(>=|≥)\s*50", text), f"{c} 缺 步数 ≥50")
            self.assertIn("duration", text.lower())

    def test_status_is_scaffold_only(self):
        for c in CODES:
            t = (DEST / c / "README_STATUS.md").read_text(encoding="utf-8")
            self.assertIn("SCAFFOLD_ONLY", t)

    def test_verify_report_says_pass(self):
        t = (DEST / "VERIFY-REPORT.md").read_text(encoding="utf-8")
        self.assertIn("**PASS**", t)
        self.assertIn("8 包全部通过", t)

    def test_master_package_present(self):
        import zipfile
        m = DEST / "FINANCIAL_EIGHT_SCAFFOLD_MASTER.zip"
        self.assertTrue(m.is_file())
        with zipfile.ZipFile(m) as z:
            self.assertIsNone(z.testzip())


if __name__ == "__main__":
    unittest.main()
