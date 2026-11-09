import tempfile
import unittest
from pathlib import Path

from fsf.ingest import build_inventory
from fsf.pack import pack_case
from fsf.scan import scan_case

try:
    from openpyxl import Workbook
    HAS_XLSX = True
except ImportError:  # pragma: no cover
    HAS_XLSX = False


def write_csv(path: Path, rows: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["id,amount"] + [f"{i},{i*10}" for i in range(1, rows + 1)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class IngestTests(unittest.TestCase):
    def test_counts_and_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "materials"
            write_csv(root / "a.csv", 2)
            write_csv(root / "copy.csv", 2)  # identical bytes -> duplicate
            inv = build_inventory(root)
            self.assertEqual(inv["file_count"], 2)
            self.assertEqual(len(inv["duplicates"]), 1)
            self.assertEqual(inv["by_ext"][".csv"], 2)
            self.assertEqual(inv["files"][0]["rows"], 2)

    @unittest.skipUnless(HAS_XLSX, "openpyxl missing")
    def test_xlsx_structure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "materials"
            root.mkdir(parents=True)
            wb = Workbook()
            ws = wb.active
            ws.title = "S"
            ws["A1"] = 100
            wb.save(root / "b.xlsx")
            inv = build_inventory(root)
            sheets = inv["files"][0]["sheets"]
            self.assertEqual(sheets[0]["name"], "S")
            self.assertEqual(sheets[0]["rows"], 1)


class ScanTests(unittest.TestCase):
    def _case(self, td, yaml_text: str) -> Path:
        case = Path(td) / "case"
        (case / "materials").mkdir(parents=True)
        write_csv(case / "materials" / "a.csv", 2)
        (case / "case.yaml").write_text(yaml_text, encoding="utf-8")
        return case

    def test_missing_required_and_rows(self):
        yaml = (
            "id: CASE-T1\n"
            "title: 测试案例\n"
            "source_type: real\n"
            "required_files:\n"
            "  - materials/a.csv\n"
            "  - materials/missing.csv\n"
            "checks:\n"
            "  - type: csv_min_rows\n"
            "    name: 明细行数\n"
            "    file: materials/a.csv\n"
            "    min_rows: 5\n"
        )
        with tempfile.TemporaryDirectory() as td:
            rep = scan_case(self._case(td, yaml))
            codes = [f["code"] for f in rep["findings"]]
            self.assertIn("missing_required", codes)
            self.assertIn("rows_short", codes)
            self.assertEqual(rep["verdict"], "FAIL")

    @unittest.skipUnless(HAS_XLSX, "openpyxl missing")
    def test_xlsx_cell_checks(self):
        yaml = (
            "id: CASE-T2\n"
            "title: 单元格检查\n"
            "source_type: real\n"
            "required_files:\n"
            "  - materials/b.xlsx\n"
            "checks:\n"
            "  - type: xlsx_cell\n"
            "    name: 合计正确\n"
            "    file: materials/b.xlsx\n"
            "    sheet: S\n"
            "    cell: A1\n"
            "    expect: 100\n"
            "    tolerance: 0.01\n"
            "  - type: xlsx_cell\n"
            "    name: 合计错误\n"
            "    file: materials/b.xlsx\n"
            "    sheet: S\n"
            "    cell: A1\n"
            "    expect: 50\n"
            "    tolerance: 0.01\n"
        )
        with tempfile.TemporaryDirectory() as td:
            case = self._case(td, yaml)
            wb = Workbook()
            wb.active.title = "S"
            wb.active["A1"] = 100
            wb.save(case / "materials" / "b.xlsx")
            rep = scan_case(case)
            codes = [f["code"] for f in rep["findings"]]
            self.assertIn("check_ok", codes)
            self.assertIn("check_mismatch", codes)


class PackTests(unittest.TestCase):
    def _case(self, td, source_type="real") -> Path:
        case = Path(td) / "CASE-P1"
        (case / "materials").mkdir(parents=True)
        write_csv(case / "materials" / "a.csv", 2)
        (case / "case.yaml").write_text(
            "id: CASE-P1\n"
            "title: 打包测试\n"
            "source_type: %s\n"
            "industry: 金融\n"
            "l2_skill: 基金估值与净值\n"
            "level3_skill: 核验估值日持仓数量\n"
            "required_files:\n"
            "  - materials/a.csv\n" % source_type,
            encoding="utf-8")
        return case

    def test_pack_layout(self):
        with tempfile.TemporaryDirectory() as td:
            case = self._case(td)
            out = Path(td) / "packs"
            pack_dir = pack_case(case, out, platform_id="TEST-1")
            for rel in ["00_meta.json", "01_public/task_prompt.md",
                        "02_platform_fields/expert_rubric.csv",
                        "03_private_review/GT/golden_response.md",
                        "05_submission/READINESS.md"]:
                self.assertTrue((pack_dir / rel).is_file(), rel)
            self.assertTrue((pack_dir / "01_public/data/a.csv").is_file())
            text = (pack_dir / "01_public/task_prompt.md").read_text(encoding="utf-8")
            self.assertIn("TEST-1", (pack_dir / "02_platform_fields/expert_profile.md").read_text(encoding="utf-8"))
            self.assertIn("打包测试", text)

    def test_pack_refuses_synthetic(self):
        with tempfile.TemporaryDirectory() as td:
            case = self._case(td, source_type="synthetic")
            with self.assertRaises(SystemExit):
                pack_case(case, Path(td) / "packs")


if __name__ == "__main__":
    unittest.main()
