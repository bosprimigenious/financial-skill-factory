"""平台表单模型测试：字段完整性、Rubric 约束、认领状态机。"""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from platform import form_schema as fs  # noqa: E402

TZ = timezone(timedelta(hours=8))
NOW = datetime(2026, 11, 9, 22, 37, 26, tzinfo=TZ)


def good_rubric():
    return [{
        "rubric_type": "必需项", "core_criterion": "PIT 判定",
        "acceptance_standard": "逐条比较 released_at 与 ts",
        "professional_judgment": "以发布日判可得性",
        "evidence_source_and_location": "M2#released_at",
        "numeric_tolerance": "0.0001", "reasonable_alternative_or_boundary": "按日粒度",
        "gate_candidate": "是"}]


def good_form():
    f = {k: "x" for k, (_l, _s, _r, kind) in fs.FIELDS.items()
         if not kind.startswith("enum:") and kind not in ("rubric_list", "files", "multi", "bool")}
    f.update({
        "skill_capability": ["查询行业高频与另类数据"],
        "prompt_attachments": ["a.zip"], "golden_attachments": ["b.zip"],
        "model_attachments": ["c.zip"], "model_version_confirmed": True,
        "rubrics": good_rubric(),
        "difficulty": "高", "rating": "基本达标", "model_duration": "少于40min",
        "need_web": "否", "web_time_limit": "否",
        "model_share_link": "https://example.com/s", "model_feedback_link": "https://example.com/f",
    })
    return f


class TestFieldModel(unittest.TestCase):
    def test_all_four_sections_present(self):
        self.assertEqual(len(fs.SECTIONS), 4)

    def test_field_count_matches_screenshot(self):
        # 22 个字段：专家信息 4、任务说明 1、作业内容 15、补充要求 2
        self.assertEqual(len(fs.FIELDS), 22)

    def test_each_field_has_section_and_label(self):
        for k, (label, section, required, kind) in fs.FIELDS.items():
            self.assertIn(section, fs.SECTIONS, k)
            self.assertTrue(label.strip(), k)
            self.assertIn(required, (True, False))


class TestFormValidation(unittest.TestCase):
    def test_good_form_passes(self):
        self.assertEqual(fs.validate_form(good_form()), [])

    def test_missing_expert_info_reported(self):
        f = good_form()
        f["expert_nickname"] = ""
        f["expert_role"] = "  "
        problems = fs.validate_form(f)
        self.assertTrue(any("个人平台昵称" in p for p in problems))
        self.assertTrue(any("专家岗位" in p for p in problems))

    def test_enum_checked(self):
        f = good_form()
        f["difficulty"] = "极高"
        self.assertTrue(any("取值非法" in p for p in fs.validate_form(f)))

    def test_rubric_required_columns(self):
        f = good_form()
        f["rubrics"] = [{"rubric_type": "必需项", "core_criterion": "只有一条"}]
        problems = fs.validate_form(f)
        self.assertTrue(any("必填列缺失" in p for p in problems))

    def test_bonus_cannot_be_gate(self):
        f = good_form()
        r = good_rubric()[0] | {"rubric_type": "加分项", "gate_candidate": "是"}
        f["rubrics"] = [r]
        self.assertTrue(any("加分项不得作为 Gate" in p for p in fs.validate_form(f)))

    def test_gate_and_bonus_limits(self):
        f = good_form()
        base = good_rubric()[0]
        f["rubrics"] = [base | {"core_criterion": f"c{i}", "gate_candidate": "是"} for i in range(4)]
        self.assertTrue(any("Gate 候选" in p for p in fs.validate_form(f)))
        f["rubrics"] = [base | {"core_criterion": f"b{i}", "rubric_type": "加分项",
                                "gate_candidate": "否"} for i in range(3)]
        self.assertTrue(any("加分项" in p for p in fs.validate_form(f)))


class TestClaimState(unittest.TestCase):
    def test_first_claim_allowed(self):
        ok, why = fs.can_claim([])
        self.assertTrue(ok, why)

    def test_second_claim_blocked_while_open(self):
        c = fs.Claim("7705055555161788179", NOW)
        ok, why = fs.can_claim([c])
        self.assertFalse(ok)
        self.assertIn("已达上限", why)

    def test_after_submit_next_claim_allowed(self):
        c = fs.Claim("7705055555161788179", NOW, submitted_at=NOW + timedelta(hours=3))
        ok, _ = fs.can_claim([c])
        self.assertTrue(ok)

    def test_window_is_48h(self):
        c = fs.Claim("x", NOW)
        self.assertEqual(c.deadline(), NOW + timedelta(hours=48))
        self.assertGreater(c.remaining(NOW).total_seconds(), 47 * 3600)


class TestRepoPack(unittest.TestCase):
    def test_fin01_pack_complete(self):
        d = REPO / "packs" / "fin01"
        for name in ("prompt.md", "ideal_steps.md", "rubric.csv", "materials_contract.md",
                     "gt.md", "STATUS.md"):
            self.assertTrue((d / name).is_file(), name)

    def test_fin01_rubric_valid(self):
        import csv
        with (REPO / "packs/fin01/rubric.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(fs._validate_rubrics(rows), [])
        self.assertTrue(any(r["rubric_type"] == "负向项" for r in rows))
        self.assertLessEqual(sum(1 for r in rows if r["rubric_type"] == "加分项"), fs.MAX_BONUS)

    def test_fin01_prompt_has_no_answer_leak(self):
        text = (REPO / "packs/fin01/prompt.md").read_text(encoding="utf-8")
        for banned in ("标准答案", "考点", "判据", "得分"):
            self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main()
