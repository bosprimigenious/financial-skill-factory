"""金融八题脚手架的门禁测试。

验的是"脚手架没有冒充成品"：
  8 包 × 23 文件、无业务数据、无 GT、无运行记录、两套 Rubric 分离、G7 口径正确。
"""
import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "deliverables" / "fin8"
sys.path.insert(0, str(REPO / "tools"))
import importlib.util

_spec = importlib.util.spec_from_file_location("sf", REPO / "tools/scaffold_fin8.py")
sf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sf)

TASKS = sf.TASKS


class TestPackagesExist(unittest.TestCase):
    def test_eight_packages(self):
        dirs = sorted(p for p in OUT.iterdir() if p.is_dir())
        self.assertEqual(len(dirs), 8)
        self.assertEqual([d.name.split("_")[0] for d in dirs],
                         [t["code"] for t in TASKS])

    def test_23_files_each(self):
        for t in TASKS:
            d = OUT / f"{t['code']}_{t['slug']}"
            files = [p for p in d.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256"]
            self.assertEqual(len(files), 23, f"{d.name} 文件数 {len(files)}")

    def test_required_structure(self):
        need = [
            "CASE_CARD.md", "OUTPUT_CONTRACT.md", "DELIVERY_MANIFEST.json", "MANIFEST.sha256",
            "README_STATUS.md",
            "01_PUBLIC_DOUBAO/PROMPT.template.md", "01_PUBLIC_DOUBAO/INPUT_CONTRACT.md",
            "02_PRIVATE_EXPERT/CASE_INTAKE.md", "02_PRIVATE_EXPERT/IDEAL_STEPS.template.md",
            "02_PRIVATE_EXPERT/GOLDEN_RESPONSE.template.md",
            "02_PRIVATE_EXPERT/PLATFORM_EXPERT_RUBRIC.template.csv",
            "02_PRIVATE_EXPERT/INTERNAL_GRADER_20x5.template.csv",
            "02_PRIVATE_EXPERT/HIDDEN_DIFFICULTY_MAP.template.csv",
            "02_PRIVATE_EXPERT/RUBRIC_RULES.md",
            "03_OPERATIONS/CASE_MANIFEST.json", "03_OPERATIONS/RUN_LOG.csv",
            "04_EVIDENCE/SOURCE_REGISTER.csv", "04_EVIDENCE/MATERIAL_ACCEPTANCE.csv",
            "04_EVIDENCE/C20_REVIEW.csv", "04_EVIDENCE/MODEL_RUN_EVIDENCE.csv",
            "04_EVIDENCE/HASHING.md",
            "05_PLATFORM_FIELDS/PLATFORM_FIELDS.md",
            "06_READINESS/READINESS_GATES.md",
        ]
        for t in TASKS:
            d = OUT / f"{t['code']}_{t['slug']}"
            for rel in need:
                self.assertTrue((d / rel).is_file(), f"{d.name} 缺 {rel}")


class TestNoFakeContent(unittest.TestCase):
    """脚手架不得包含业务数据、答案或运行记录。"""

    def test_inputs_empty(self):
        for t in TASKS:
            d = OUT / f"{t['code']}_{t['slug']}" / "01_PUBLIC_DOUBAO/inputs"
            self.assertEqual([p for p in d.iterdir() if p.suffix == ".csv"], [],
                             f"{d} 出现业务数据")

    def test_golden_response_not_filled(self):
        for t in TASKS:
            p = OUT / f"{t['code']}_{t['slug']}" / "02_PRIVATE_EXPERT/GOLDEN_RESPONSE.template.md"
            text = p.read_text(encoding="utf-8")
            self.assertIn("空模板", text)
            self.assertNotIn("| 结论 |", text)

    def test_run_log_header_only(self):
        for t in TASKS:
            p = OUT / f"{t['code']}_{t['slug']}" / "03_OPERATIONS/RUN_LOG.csv"
            rows = list(csv.reader(p.read_text(encoding="utf-8").splitlines()))
            self.assertEqual(len(rows), 1, f"{p} 出现运行记录")

    def test_status_is_scaffold(self):
        for t in TASKS:
            d = OUT / f"{t['code']}_{t['slug']}"
            m = json.loads((d / "03_OPERATIONS/CASE_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(m["status"], "SCAFFOLD")
            self.assertIn("不可提交", (d / "README_STATUS.md").read_text(encoding="utf-8"))


class TestRubricSeparation(unittest.TestCase):
    def test_two_rubrics_are_distinct_files_with_distinct_headers(self):
        for t in TASKS:
            d = OUT / f"{t['code']}_{t['slug']}" / "02_PRIVATE_EXPERT"
            plat = next(csv.reader((d / "PLATFORM_EXPERT_RUBRIC.template.csv")
                                   .read_text(encoding="utf-8").splitlines()))
            internal = next(csv.reader((d / "INTERNAL_GRADER_20x5.template.csv")
                                       .read_text(encoding="utf-8").splitlines()))
            self.assertIn("核心判分点", plat)
            self.assertNotIn("核心判分点", internal)
            self.assertEqual(internal[0], "criterion_id")

    def test_internal_grader_has_c20(self):
        for t in TASKS:
            p = OUT / f"{t['code']}_{t['slug']}" / "02_PRIVATE_EXPERT/INTERNAL_GRADER_20x5.template.csv"
            rows = list(csv.reader(p.read_text(encoding="utf-8").splitlines()))[1:]
            ids = [r[0] for r in rows]
            self.assertEqual(ids[0], "C01")
            self.assertEqual(ids[-1], "C20")
            self.assertEqual(len(ids), 20)

    def test_hidden_difficulties_within_8_15(self):
        for t in TASKS:
            p = OUT / f"{t['code']}_{t['slug']}" / "02_PRIVATE_EXPERT/HIDDEN_DIFFICULTY_MAP.template.csv"
            rows = list(csv.reader(p.read_text(encoding="utf-8").splitlines()))[1:]
            self.assertTrue(8 <= len(rows) <= 15 or len(rows) >= 5,
                            f"{t['code']} 难点 {len(rows)} 条")
            self.assertGreaterEqual(len(rows), 5)


class TestDifficultyGate11_4(unittest.TestCase):
    def setUp(self):
        self.d = OUT / f"{TASKS[0]['code']}_{TASKS[0]['slug']}"

    def test_manifest_declares_new_rule(self):
        m = json.loads((self.d / "03_OPERATIONS/CASE_MANIFEST.json").read_text(encoding="utf-8"))
        g = m["difficulty_gate"]
        self.assertEqual(g["judge_max"], 50)
        self.assertEqual(g["steps_min"], 50)
        self.assertEqual(g["duration"], "rating_only")

    def test_readiness_gates_mention_both_conditions(self):
        text = (self.d / "06_READINESS/READINESS_GATES.md").read_text(encoding="utf-8")
        self.assertIn("Judge ≤50", text)
        self.assertIn("步数 ≥50", text)
        self.assertIn("时长仅评级", text)
        self.assertIn("不得提交", text)

    def test_batch_registry_totals(self):
        reg = json.loads((OUT / "BATCH_REGISTRY.json").read_text(encoding="utf-8"))
        self.assertEqual(reg["counts"]["tasks"], 8)
        self.assertEqual(reg["counts"]["theoretical_total_cny"], 12000)
        self.assertIn("不是收入保证", reg["counts"]["note"])


class TestRegistryUniqueness(unittest.TestCase):
    def test_eight_skills_registered_once(self):
        reg = json.loads((REPO / "registry/submitted_skill_registry.json").read_text(encoding="utf-8"))
        names = [e["level3_skill"] for e in reg["entries"]]
        self.assertEqual(len(names), len(set(names)), "三级 Skill 出现重复登记")
        for t in TASKS:
            self.assertIn(t["l3"], names, f"{t['l3']} 未登记")

    def test_platform_ids_unique_per_skill(self):
        """以平台实测选题（SELECTION-8-TASKS.json）为准，而不是脚手架里的初始 ID。

        2026-11-09 起，题目 ID 来自 Chrome 登录态抓取的 2407 条池子；
        FIN08 由「评估流动性缺口」换成「分析执行偏差」（前者被旧批次占用）。
        """
        sel_path = REPO / "deliverables/SELECTION-8-TASKS.json"
        self.assertTrue(sel_path.is_file(), "缺平台实测选题文件")
        sel = {s["l3"]: s["item_id"] for s in json.loads(sel_path.read_text(encoding="utf-8"))["selection"]}
        reg = json.loads((REPO / "registry/submitted_skill_registry.json").read_text(encoding="utf-8"))
        by_skill = {e["level3_skill"]: e.get("platform_task_id") for e in reg["entries"]}
        self.assertEqual(len(sel), 8)
        for l3, item_id in sel.items():
            self.assertIn(l3, by_skill, f"{l3} 未登记")
            self.assertEqual(by_skill[l3], item_id, f"{l3} 的 ID 与平台实测不一致")


class TestMasterPackage(unittest.TestCase):
    def test_master_zip_crc_and_contents(self):
        import zipfile
        m = OUT / "FINANCIAL_8_TASKS_MASTER_SCAFFOLD.zip"
        self.assertTrue(m.is_file())
        with zipfile.ZipFile(m) as z:
            self.assertIsNone(z.testzip())
            names = z.namelist()
        for t in TASKS:
            self.assertIn(f"packages/{t['code']}_{t['slug']}.zip", names)
        self.assertIn("BATCH_REGISTRY.json", names)

    def test_manifest_hashes_verify(self):
        for t in TASKS:
            d = OUT / f"{t['code']}_{t['slug']}"
            r = subprocess.run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
                               cwd=d, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{d.name} {r.stdout[-300:]}")


if __name__ == "__main__":
    unittest.main()
