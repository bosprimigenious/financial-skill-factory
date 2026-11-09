import json
import tempfile
import unittest
from pathlib import Path
from tools.new_task import create_case
from tools.package_batch import package, load, BATCH

class FinancialBatchPipelineTests(unittest.TestCase):
    def test_selected_batch_has_eight_unique_skills(self):
        root=Path(__file__).resolve().parents[1]
        batch=json.loads((root/"finance/batch/selected_tasks.json").read_text(encoding="utf-8"))
        self.assertEqual(len(batch["selected_tasks"]),8)
        self.assertEqual(len({x["third_level_skill"] for x in batch["selected_tasks"]}),8)
        self.assertEqual(len({x["platform_task_id"] for x in batch["selected_tasks"]}),8)
        registry=json.loads((root/"registry/submitted_skill_registry.json").read_text(encoding="utf-8"))
        by_id={str(x["platform_task_id"]):x for x in registry["entries"]}
        for item in batch["selected_tasks"]:
            entry=by_id[str(item["platform_task_id"])]
            self.assertEqual(entry["level3_skill"],item["third_level_skill"])
            self.assertEqual(entry["l2_skill"],item["second_level_skill"])
            self.assertIn(entry["status"],{"draft","carried_over_previous"})

    def test_generator_creates_case_scaffold(self):
        with tempfile.TemporaryDirectory() as td:
            case=create_case("FIN01_ALT_DATA",Path(td))
            self.assertTrue((case/"01_PUBLIC_DOUBAO/PROMPT.md").is_file())
            self.assertTrue((case/"02_PRIVATE_EXPERT/GOLDEN_RESPONSE.md").is_file())
            self.assertTrue((case/"04_EVIDENCE/MODEL_RUN_EVIDENCE.csv").is_file())
            self.assertTrue((case/"DELIVERY_MANIFEST.json").is_file())
            self.assertTrue((case/"MANIFEST.sha256").is_file())
            m=json.loads((case/"03_OPERATIONS/CASE_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(m["readiness_status"],"SCAFFOLD_ONLY")
            self.assertEqual(m["platform_task_id"],"7705055555161788179")

    def test_release_package_fails_closed_for_scaffold_cases(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            batch=load(BATCH)
            for item in batch["selected_tasks"]:
                create_case(item["case_code"],root)
            with self.assertRaisesRegex(ValueError,"not AUTHOR_QA_PASS"):
                package(root,root/"dist","release")

    def test_generator_rejects_unreserved_or_mismatched_skill(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            registry=root/"registry.json"
            original=json.loads((Path(__file__).resolve().parents[1]/"registry/submitted_skill_registry.json").read_text(encoding="utf-8"))
            original["entries"][0]["level3_skill"]="WRONG SKILL"
            registry.write_text(json.dumps(original),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"registry mismatch"):
                create_case("FIN01_ALT_DATA",root,registry_path=registry,submitted_registry_path=registry)

    def test_generator_rejects_unknown_case(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                create_case("FIN99_UNKNOWN",Path(td))

if __name__=="__main__": unittest.main()
