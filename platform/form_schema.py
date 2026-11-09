"""平台作答页的真实字段模型（2026-11-09 从 FIN01 作答页逐项抄录）。

存在理由：产线此前按"六材料"想象提交，实际平台是**一张长表单 + 硬性状态机**。
本模块把表单和领取规则编码成机器可校验的结构，避免再靠记忆填写。

状态机（实测）：
  * 同时只能持有 1 道已认领未提交的题（提示：已达上限，提交后可继续认领）
  * 认领后进入"处理中"，页面显示释放倒计时（实测 47h50m ⇒ 48 小时窗口）
  * 提交后进入"待修改/已提交"；未提交不可领下一题
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=8))

# 作答页四个区块（截图顺序）
SECTIONS = ["1_专家信息", "2_任务说明", "3_作业内容", "4_补充要求"]

# 每个字段：key -> (中文名, 所属区块, 必填, 类型)
FIELDS: dict[str, tuple[str, str, bool, str]] = {
    # 1 专家信息
    "expert_nickname": ("个人平台昵称", "1_专家信息", True, "text"),
    "expert_feishu": ("飞书联系方式", "1_专家信息", True, "text"),
    "expert_role": ("专家岗位", "1_专家信息", True, "text"),
    "expert_credential": ("专家资质说明", "1_专家信息", True, "text"),
    # 2 任务说明
    "skill_capability": ("本 Task 对应的 Skill 能力（多选）", "2_任务说明", True, "multi"),
    # 3 作业内容
    "prompt_text": ("提示词", "3_作业内容", True, "longtext"),
    "prompt_attachments": ("提示词附件", "3_作业内容", True, "files"),
    "ideal_steps": ("理想执行步骤（Ideal Steps）", "3_作业内容", True, "longtext"),
    "golden_response": ("理想回复文本（golden response）", "3_作业内容", True, "longtext"),
    "golden_attachments": ("理想回复附件", "3_作业内容", True, "files"),
    "rubrics": ("评分标准（rubrics）", "3_作业内容", True, "rubric_list"),
    "model_version_confirmed": ("模型版本确认", "3_作业内容", True, "bool"),
    "model_output_text": ("豆包 2.1 Pro 输出文本", "3_作业内容", True, "longtext"),
    "model_share_link": ("回答分享链接", "3_作业内容", True, "url"),
    "model_feedback_link": ("回答反馈链接", "3_作业内容", True, "url"),
    "model_attachments": ("豆包输出附件", "3_作业内容", True, "files"),
    "difficulty": ("难度（低/中/高）", "3_作业内容", True, "enum:低/中/高"),
    "rating": ("回答评级（不达标/基本达标/优秀）", "3_作业内容", True, "enum:不达标/基本达标/优秀"),
    "rating_explanation": ("回答评价说明", "3_作业内容", True, "longtext"),
    "model_duration": ("模型运行时长（少于40min/40min及以上）", "3_作业内容", True, "enum:少于40min/40min及以上"),
    # 4 补充要求
    "need_web": ("是否需要联网（是/否）", "4_补充要求", True, "enum:是/否"),
    "web_time_limit": ("联网信息是否有时间限制（是/否）", "4_补充要求", True, "enum:是/否"),
}

RUBRIC_COLUMNS = ["rubric_type", "core_criterion", "acceptance_standard",
                  "professional_judgment", "evidence_source_and_location",
                  "numeric_tolerance", "reasonable_alternative_or_boundary", "gate_candidate"]

RUBRIC_REQUIRED = ["core_criterion", "acceptance_standard", "professional_judgment",
                   "evidence_source_and_location"]
RUBRIC_TYPES = ("必需项", "负向项", "加分项")
MAX_GATES = 3
MAX_BONUS = 2


@dataclass
class Claim:
    item_id: str
    claimed_at: datetime
    submitted_at: datetime | None = None
    window_hours: int = 48

    @property
    def open(self) -> bool:
        return self.submitted_at is None

    def deadline(self) -> datetime:
        return self.claimed_at + timedelta(hours=self.window_hours)

    def remaining(self, now: datetime | None = None) -> timedelta:
        return self.deadline() - (now or datetime.now(TZ))


class ClaimLimitError(RuntimeError):
    """同时只允许 1 道未提交的题。"""


def can_claim(existing: list[Claim]) -> tuple[bool, str]:
    open_claims = [c for c in existing if c.open]
    if len(open_claims) >= 1:
        return False, (f"已达上限：{open_claims[0].item_id} 未提交；"
                       f"剩余 {open_claims[0].remaining()}；提交后才能认领下一题")
    return True, "ok"


def validate_form(form: dict) -> list[str]:
    """返回缺失/非法字段的中文说明；空列表表示可提交。"""
    problems: list[str] = []
    for key, (label, section, required, kind) in FIELDS.items():
        v = form.get(key)
        if required and (v is None or (isinstance(v, str) and not v.strip()) or v == []):
            problems.append(f"[{section}] {label} 为空")
            continue
        if v is None:
            continue
        if kind.startswith("enum:"):
            allowed = kind.split(":", 1)[1].split("/")
            if str(v) not in allowed:
                problems.append(f"[{section}] {label} 取值非法：{v}（应为 {'/'.join(allowed)}）")
        elif kind == "rubric_list":
            problems.extend(_validate_rubrics(v))
    return problems


def _validate_rubrics(items: list[dict]) -> list[str]:
    out: list[str] = []
    if not isinstance(items, list) or not items:
        return ["[3_作业内容] 评分标准至少完整填写 1 条"]
    gates = sum(1 for i in items if str(i.get("gate_candidate", "")).strip() not in ("", "否"))
    bonus = sum(1 for i in items if i.get("rubric_type") == "加分项")
    if gates > MAX_GATES:
        out.append(f"[3_作业内容] Gate 候选 {gates} 条，超过上限 {MAX_GATES}")
    if bonus > MAX_BONUS:
        out.append(f"[3_作业内容] 加分项 {bonus} 条，超过上限 {MAX_BONUS}")
    for n, it in enumerate(items, 1):
        if it.get("rubric_type") not in RUBRIC_TYPES:
            out.append(f"[Rubric {n}] 类型必须是 {'/'.join(RUBRIC_TYPES)}")
        for col in RUBRIC_REQUIRED:
            if not str(it.get(col, "")).strip():
                out.append(f"[Rubric {n}] 必填列缺失：{col}")
        if it.get("rubric_type") == "加分项" and str(it.get("gate_candidate", "")).strip() not in ("", "否"):
            out.append(f"[Rubric {n}] 加分项不得作为 Gate")
    return out


def render_export(form: dict) -> str:
    """把表单渲染成可粘贴的提交稿（便于人工复核与归档）。"""
    lines = ["# 平台提交稿", ""]
    for section in SECTIONS:
        lines.append(f"## {section}")
        for key, (label, sec, _req, _kind) in FIELDS.items():
            if sec != section:
                continue
            v = form.get(key, "")
            if isinstance(v, list) and v and isinstance(v[0], dict):
                lines.append(f"- **{label}**：{len(v)} 条")
                for i, it in enumerate(v, 1):
                    lines.append(f"  {i}. {it.get('core_criterion', '')} ｜ {it.get('acceptance_standard', '')}")
            elif isinstance(v, list):
                lines.append(f"- **{label}**：{'、'.join(map(str, v)) or '（空）'}")
            else:
                text = str(v or "（空）")
                lines.append(f"- **{label}**：{text[:400]}")
        lines.append("")
    return "\n".join(lines)
