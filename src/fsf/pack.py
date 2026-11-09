"""Create a six-material pack skeleton from a validated case."""
from __future__ import annotations

import shutil
from pathlib import Path

from .util import load_case, write_json

TEMPLATES = Path(__file__).parent / "templates"
LAYOUT = {
    "01_public/task_prompt.md": "task_prompt.md",
    "02_platform_fields/expert_profile.md": "expert_profile.md",
    "02_platform_fields/expert_rubric.csv": "expert_rubric.csv",
    "02_platform_fields/hidden_difficulties.md": "hidden_difficulties.md",
    "02_platform_fields/ideal_steps.md": "ideal_steps.md",
    "02_platform_fields/rating.md": "rating.md",
    "03_private_review/GT/golden_response.md": "golden_response.md",
}
DIRS = [
    "01_public/data",
    "02_platform_fields",
    "03_private_review/GT",
    "04_evidence/downloads",
    "04_evidence/c20",
    "05_submission/01_prompt_attachments",
    "05_submission/02_ideal_attachments",
    "05_submission/03_doubao_outputs",
]


def render(text: str, mapping: dict) -> str:
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def pack_case(case_dir: Path, out_root: Path, platform_id: str | None = None,
              task_name: str | None = None) -> Path:
    case = load_case(case_dir)
    if case.get("source_type") == "synthetic":
        raise SystemExit("拒绝打包：source_type=synthetic 只能做工程夹具，不能进交付包")
    task_id = str(case.get("id") or case_dir.name)
    pack_dir = out_root / task_id
    if pack_dir.exists():
        raise SystemExit(f"拒绝覆盖已存在的包：{pack_dir}")
    for sub in DIRS:
        (pack_dir / sub).mkdir(parents=True, exist_ok=True)

    mapping = {
        "TASK_ID": task_id,
        "TASK_NAME": task_name or case.get("title") or task_id,
        "L1": case.get("industry", "金融"),
        "L2": case.get("l2_skill", "TBD"),
        "L3": case.get("level3_skill", "TBD"),
        "PLATFORM_ID": platform_id or case.get("platform_task_id", "TBD"),
        "CASE_ID": case.get("id"),
    }
    for rel, tpl in LAYOUT.items():
        target = pack_dir / rel
        target.write_text(render((TEMPLATES / tpl).read_text(encoding="utf-8"), mapping),
                          encoding="utf-8")

    # copy materials into the public data slot (never into GT/private)
    materials = case_dir / "materials"
    if materials.is_dir():
        for src in sorted(materials.rglob("*")):
            if src.is_file():
                dst = pack_dir / "01_public/data" / src.relative_to(materials)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    write_json(pack_dir / "00_meta.json", {
        "task_id": task_id,
        "task_name": mapping["TASK_NAME"],
        "platform_task_id": mapping["PLATFORM_ID"],
        "industry": mapping["L1"],
        "l2_skill": mapping["L2"],
        "level3_skill": mapping["L3"],
        "case_id": case.get("id"),
        "source_type": case.get("source_type"),
        "status": "DRAFT",
        "as_of": case.get("as_of"),
    })
    (pack_dir / "05_submission").mkdir(exist_ok=True)
    (pack_dir / "05_submission" / "READINESS.md").write_text(
        "# 提交前检查\n\n"
        "- [ ] 题面无答案泄露\n- [ ] GT 可复算\n- [ ] rubric 字段齐全（必需+负向 5–12，加分≤2，Gate≤3）\n"
        "- [ ] 三类附件槽位不混\n- [ ] 豆包工作任务模式 2.1Pro / 云电脑 / 推理强度高 实跑留档\n"
        "- [ ] judge ≤50 且单轮调用步数 ≥50 有证据\n", encoding="utf-8")
    return pack_dir
