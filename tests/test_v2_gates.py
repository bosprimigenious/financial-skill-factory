"""V2 · 门禁与难度预检测试。"""
import json
import tempfile
import unittest
from pathlib import Path

from case_intake import authenticity_gate, pii_checker, source_registry
from evaluation import difficulty_preflight, mutation_test
from task_architect.complexity import DecisionDAG, Node

RULE = {"judge_max": 50, "steps_min": 50, "time_min_seconds": 2400, "combine": "any_two"}


def rec(score=46, steps=22, seconds=2916):
    return difficulty_preflight.RunRecord("r1", "t1", "a" * 64, "豆包2.1Pro", "工作任务",
                                          score, steps, seconds)


class TestDifficulty(unittest.TestCase):
    def test_real_case_passes_any_two_fails_all(self):
        out = difficulty_preflight.preflight(rec(), RULE)
        self.assertEqual(out["verdict"], "PASS")                  # 现行书面口径
        self.assertEqual(out["verdict_by_reading"]["all"], "FAIL")  # 改造建议口径
        self.assertEqual(out["verdict_by_reading"]["any_two"], "PASS")

    def test_env_failure_invalid(self):
        r = difficulty_preflight.RunRecord("r2", "t1", "b" * 64, "m", "mode", 10, 60, 3000,
                                           status="ENV_FAILURE")
        with self.assertRaises(ValueError):
            r.validate()

    def test_unverifiable_steps_marked(self):
        out = difficulty_preflight.preflight(rec(steps=None, seconds=100), RULE)
        self.assertIn("steps", out["unverifiable"])
        self.assertEqual(out["verdict"], "FAIL")

    def test_prompt_hash_required(self):
        r = difficulty_preflight.RunRecord("r3", "t1", "", "m", "mode", 10, 60, 3000)
        with self.assertRaises(ValueError):
            r.validate()

    def test_rule_loader(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "rule.yaml"
            p.write_text("judge_max: 50\nsteps_min: 50\ntime_min_seconds: 2400\ncombine: all\n",
                         encoding="utf-8")
            r = difficulty_preflight.load_rule(p)
            self.assertEqual(r["combine"], "all")
            self.assertEqual(r["judge_max"], 50)


class TestMutation(unittest.TestCase):
    def test_key_number_mutation_flips_score(self):
        expected = {"net_capital": ("4580.00", "0.01"), "nav": ("1.200000", "0.000001")}
        weights = {"net_capital": 60, "nav": 40}
        res = mutation_test.run(expected, weights)
        self.assertTrue(mutation_test.summarise(res)["ok"], res)

    def test_zero_tolerance_still_detects(self):
        res = mutation_test.run({"x": ("100", "0")}, {"x": 100})
        self.assertTrue(res[0].passed)


class TestCaseIntake(unittest.TestCase):
    def test_material_change_detected(self):
        with tempfile.TemporaryDirectory() as d:
            mat = Path(d) / "materials"
            mat.mkdir()
            (mat / "a.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            src = source_registry.CaseSource.register(
                d, title="t", provenance="https://example.com/x", source_type="public",
                collected_at="2026-11-09T00:00:00+08:00", released_at="2026-10-01")
            source_registry.CaseSource.verify_hashes(d, src)
            (mat / "a.csv").write_text("a,b\n1,3\n", encoding="utf-8")
            with self.assertRaises(source_registry.MaterialChanged):
                source_registry.CaseSource.verify_hashes(d, src)

    def test_synthetic_without_disclosure_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "materials").mkdir()
            src = source_registry.CaseSource(
                case_id=Path(d).name, title="t", provenance="base/xx?table=yy",
                source_type="synthetic", collected_at="2026-11-09T00:00:00+08:00",
                synthetic_disclosed_in_prompt=False)
            g = authenticity_gate.check(src=src, prompt_text="你是分析师。",
                                        level3_skill="测试skill")
            self.assertFalse(g.passed)
            self.assertTrue(any(r == "A5" for r, _ in g.failures))

    def test_public_requires_release_date(self):
        src = source_registry.CaseSource(
            case_id="c", title="t", provenance="https://x", source_type="public",
            collected_at="2026-11-09T00:00:00+08:00", synthetic_disclosed_in_prompt=True)
        g = authenticity_gate.check(src=src, prompt_text="匿名", level3_skill="sk")
        self.assertTrue(any(r == "A4" for r, _ in g.failures))

    def test_pii_blocking(self):
        hits = pii_checker.scan_text("联系人 13812345678 身份证 11010119900307123X")
        self.assertEqual(len(pii_checker.blocking(hits)), 2)
        self.assertTrue(all("*" in h.masked for h in hits))


class TestComplexity(unittest.TestCase):
    def dag(self):
        g = DecisionDAG()
        g.add(Node("e1", "evidence", "附件3 漏洞记录", evidence_sources=("附件3",)))
        g.add(Node("e2", "evidence", "附件4 权限核查", evidence_sources=("附件4",)))
        g.add(Node("j1", "judgment", "漏洞维度定级", evidence_sources=("附件3", "附件10"),
                   time_dependent=True, sensitive_to=("期间外排除",)))
        g.add(Node("j2", "judgment", "综合定级", evidence_sources=("附件10",),
                   constraints=("关键性上调",)))
        g.add(Node("a1", "action", "处置与复评"))
        g.link("e1", "j1"); g.link("e2", "j1"); g.link("j1", "j2"); g.link("j2", "a1")
        return g

    def test_metrics_and_propagation(self):
        m = self.dag().metrics()
        self.assertEqual(m["E"], 3)          # 附件3/附件4/附件10
        self.assertEqual(m["C"], 1)          # j1 多源
        self.assertEqual(m["T"], 1)
        self.assertEqual(m["propagation_max"], 2)   # j1 -> j2 -> a1
        self.assertEqual(m["A"], 1)

    def test_cycle_rejected(self):
        g = self.dag(); g.link("a1", "j1")
        with self.assertRaises(ValueError):
            g.validate()

    def test_orphan_evidence_rejected(self):
        g = DecisionDAG(); g.add(Node("e9", "evidence", "孤立证据"))
        with self.assertRaises(ValueError):
            g.validate()

    def test_flags_when_too_thin(self):
        g = DecisionDAG()
        g.add(Node("e1", "evidence", "单一附件", evidence_sources=("A",)))
        g.add(Node("j1", "judgment", "单点判断", evidence_sources=("A",)))
        g.link("e1", "j1")
        self.assertTrue(g.complexity_flags())


if __name__ == "__main__":
    unittest.main()
