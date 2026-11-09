"""V2 · Rubric 生成与 QA 测试。"""
import unittest

from evaluation import rubric_qa
from generators import isolation, rubric_builder

PROMPT = """你是某银行信息科技风险管理岗。

【任务：交付物】
D1 定级表
D2 处置名单

【交付要求（硬性）】
1. 逐户给出综合等级与处置意见，并给出入选与未入选两份名单。
2. 给出每个格子的取证记录编号，结论须能追溯到原件。
3. 给出优先级排序的计算式，并写明并列处理方式。
4. 逐条列出期间外记录并写明排除依据。
5. 对证据缺失事项单列待核，写明缺什么、由谁补。
6. 写明审批岗位、执行时限与停止条件。
7. 给出计数勾稽：分部之和等于总数。
8. 给出档位与处置用词的自定映射表。
"""

FIELDS = {"附件1_供应商主数据.csv": ["供应商编号", "合同止日"],
          "附件3_漏洞记录.csv": ["漏洞ID", "发现日", "状态"],
          "附件10_定级标准.csv": ["判定规则"]}


class TestRubricBuilder(unittest.TestCase):
    def test_weights_sum_to_100(self):
        r = rubric_builder.build(task_id="T1", prompt=PROMPT, materials_fields=FIELDS)
        self.assertEqual(len(r.items), 8)
        self.assertEqual(r.total, 100)

    def test_layers_assigned(self):
        r = rubric_builder.build(task_id="T1", prompt=PROMPT, materials_fields=FIELDS)
        layers = {i.layer for i in r.items}
        self.assertIn("L1", layers)
        self.assertIn("L3", layers)

    def test_evidence_anchor_found(self):
        r = rubric_builder.build(task_id="T1", prompt=PROMPT, materials_fields=FIELDS)
        anchored = [i for i in r.items if "需人工补" not in i.evidence_anchor]
        self.assertGreaterEqual(len(anchored), 1)

    def test_bad_weights_rejected(self):
        with self.assertRaises(ValueError):
            rubric_builder.build(task_id="T1", prompt=PROMPT, materials_fields=FIELDS,
                                 weights=[10, 10, 10, 10, 10, 10, 10, 10])

    def test_no_requirements_rejected(self):
        with self.assertRaises(ValueError):
            rubric_builder.build(task_id="T2", prompt="随便一段没有交付要求的文字",
                                 materials_fields={})

    def test_rubric_never_reads_gt(self):
        r = rubric_builder.build(task_id="T1", prompt=PROMPT, materials_fields=FIELDS)
        self.assertNotIn("gt", (r.to_dict() or {}))
        self.assertTrue(hasattr(rubric_builder, "build"))


class TestRubricQA(unittest.TestCase):
    def setUp(self):
        self.r = rubric_builder.build(task_id="T1", prompt=PROMPT, materials_fields=FIELDS)

    def test_coverage_passes(self):
        self.assertEqual([f for f in rubric_qa.coverage(self.r, PROMPT)], [])

    def test_missing_requirement_detected(self):
        r2 = rubric_builder.Rubric("T3", self.r.items[:5])
        f = rubric_qa.coverage(r2, PROMPT)
        self.assertTrue(f)

    def test_duplicate_detected(self):
        it = self.r.items[0]
        r2 = rubric_builder.Rubric("T4", [it, rubric_builder.RubricItem(
            "X", it.layer, it.statement, 50, evidence_anchor=it.evidence_anchor)])
        self.assertTrue(rubric_qa.duplicate(r2))

    def test_core_failure_requires_zero_example(self):
        f = rubric_qa.core_failure(self.r)
        self.assertTrue(f)   # 本样例未写 0 分反例，应被抓出
        self.r.items[0].zero_example = "把未触发判为触发"
        self.assertLess(len(rubric_qa.core_failure(self.r)), len(f))

    def test_run_all_shape(self):
        res = rubric_qa.run_all(self.r, PROMPT)
        for k in ("findings", "fail", "warn", "ok"):
            self.assertIn(k, res)


class TestIsolation(unittest.TestCase):
    def test_disjoint_ok(self):
        isolation.assert_disjoint(("materials", "verifiers"), ("prompt", "materials", "rules"))

    def test_gt_and_rubric_cannot_share(self):
        with self.assertRaises(isolation.IsolationError):
            isolation.assert_disjoint(("materials", "gt"), ("prompt", "gt"))

    def test_unknown_input_rejected(self):
        with self.assertRaises(isolation.IsolationError):
            isolation.assert_disjoint(("materials", "answers_key"), ())

    def test_seal_and_verify(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            mat = Path(d) / "m"; mat.mkdir(); (mat / "a.csv").write_text("x,1\n", encoding="utf-8")
            rec = isolation.seal("gt", ("materials",), {"materials": mat}, d)
            self.assertTrue(rec["input_hashes"])
            p = Path(d) / "seals" / "gt.seal.json"
            self.assertTrue(isolation.verify_seal(p, {"materials": mat}))
            (mat / "a.csv").write_text("x,2\n", encoding="utf-8")
            self.assertFalse(isolation.verify_seal(p, {"materials": mat}))


if __name__ == "__main__":
    unittest.main()
