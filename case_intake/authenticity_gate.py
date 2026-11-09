"""Stage 0 · 真实性 / 合规门禁。

七条规则，任一条不过即拒绝进入生成（不是警告，是拒绝）。
规则码固定，便于在运行记录与申诉材料里引用。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .pii_checker import scan_text

RULES = {
    "A1": "来源可定位（URL / Base·table 坐标 / 合同编号）",
    "A2": "source_type 合法",
    "A3": "real 必须有授权与脱敏标记",
    "A4": "public 必须有发布日",
    "A5": "synthetic 必须在题面标注合成",
    "A6": "材料内无高危 PII",
    "A7": "三级 Skill 未被占用（由 registry 传入占用集）",
}


@dataclass
class GateResult:
    case_id: str
    passed: bool
    failures: list[tuple[str, str]] = field(default_factory=list)   # (rule, reason)
    warnings: list[str] = field(default_factory=list)

    def raise_if_failed(self) -> None:
        if not self.passed:
            detail = "; ".join(f"{r}: {m}" for r, m in self.failures)
            raise PermissionError(f"真实性门禁未通过 [{self.case_id}] {detail}")


def check(*, src, prompt_text: str, materials_text: str = "", occupied_skills=(),
          level3_skill: str = "") -> GateResult:
    f: list[tuple[str, str]] = []
    w: list[str] = []

    if not (src.provenance or "").strip():
        f.append(("A1", "provenance 为空"))
    elif not re.search(r"https?://|/table=|base/|\b[A-Z]{2,}-\d+", src.provenance):
        w.append(f"A1 provenance 可疑（{'无法识别为坐标'}）：{src.provenance[:60]}")

    if src.source_type not in ("real", "public", "synthetic"):
        f.append(("A2", f"source_type={src.source_type!r}"))

    if src.source_type == "real":
        if not src.authorized:
            f.append(("A3", "real 案例未标记 authorized"))
        if not src.desensitized:
            f.append(("A3", "real 案例未标记 desensitized"))

    if src.source_type == "public" and not src.released_at:
        f.append(("A4", "public 案例缺少 released_at"))

    if src.source_type == "synthetic":
        if not src.synthetic_disclosed_in_prompt:
            f.append(("A5", "synthetic 案例未声明已标注，或题面未写合成说明"))
        if "合成" not in prompt_text and "模拟" not in prompt_text and "匿名" not in prompt_text:
            f.append(("A5", "题面正文未见合成/模拟/匿名说明"))

    hits = scan_text(materials_text, where="materials")
    if hits:
        f.append(("A6", f"高危 PII {len(hits)} 处：{hits[:3]}"))

    if level3_skill:
        if level3_skill in set(occupied_skills):
            f.append(("A7", f"三级 Skill 已被占用：{level3_skill}"))
    else:
        f.append(("A7", "未提供 level3_skill"))

    return GateResult(src.case_id, not f, f, w)


def occupied_from(registry_path: str) -> set[str]:
    """从 submitted_skill_registry.json 取占用集（status != released）。"""
    import json
    from pathlib import Path
    p = Path(registry_path)
    if not p.is_file():
        return set()
    data = json.loads(p.read_text(encoding="utf-8"))
    OCCUPYING = {"draft", "submitted", "carried_over_previous", "locked"}
    out = set()
    for e in data.get("entries", []):
        if e.get("status") in OCCUPYING and e.get("level3_skill"):
            out.add(e["level3_skill"])
    return out
