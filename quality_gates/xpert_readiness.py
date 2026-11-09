"""Stage 6 · 提交门禁（外部事实驱动）。

与 V1 `tools/verify_pack.py` 的区别：这里不读"我自己写的断言"，
只读**外部可核对的东西**——材料文件与行数、GT 文件与表数、隔离回执、运行记录、考点权重。

任一 blocker 存在即 NOT READY。
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Readiness:
    task_id: str
    blockers: list[str] = field(default_factory=list)
    checks: list[tuple[str, bool, str]] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append((name, ok, detail))
        if not ok:
            self.blockers.append(f"{name}: {detail}")

    @property
    def ready(self) -> bool:
        return not self.blockers


SIX_MATERIALS = ("01_public/task_prompt.md", "01_public/data", "02_platform_fields/expert_rubric.md",
                 "02_platform_fields/ideal_steps.md", "03_private_review/GT", "04_evidence")


def _csv_rows(p: Path) -> int:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return max(0, sum(1 for _ in csv.reader(f)) - 1)


def evaluate(pack_dir: str | Path, *, expected_rows: dict[str, int] | None = None,
             run_log: str | Path | None = None) -> Readiness:
    p = Path(pack_dir)
    r = Readiness(p.name)

    for rel in SIX_MATERIALS:
        r.add(f"六材料·{rel}", (p / rel).exists(), "缺失")

    data = p / "01_public/data"
    if data.is_dir():
        files = [f for f in data.iterdir() if f.is_file()]
        r.add("材料非空", bool(files), "01_public/data 为空")
        if expected_rows:
            for name, n in expected_rows.items():
                f = data / name
                if not f.is_file():
                    r.add(f"材料行数·{name}", False, "缺文件")
                elif f.suffix == ".csv":
                    got = _csv_rows(f)
                    r.add(f"材料行数·{name}", got == n, f"{got}≠{n}")

    gt = p / "03_private_review/GT"
    gt_files = [f for f in gt.iterdir() if f.is_file()] if gt.is_dir() else []
    r.add("GT 存在", bool(gt_files), "GT 目录为空")

    seals = p / "04_evidence/seals"
    for art in ("gt", "rubric"):
        r.add(f"隔离回执·{art}", (seals / f"{art}.seal.json").exists(),
              "缺回执：无法证明生成时未读取对方产物")

    rub = p / "02_platform_fields/expert_rubric.md"
    if rub.is_file():
        txt = rub.read_text(encoding="utf-8")
        import re
        ws = [int(x) for x in re.findall(r"｜(\d+) ?分】|（(\d+) ?分）", txt) for x in x if x]
        r.add("考点权重=100", (sum(ws) == 100) if ws else False,
              f"解析到 {len(ws)} 条，合计 {sum(ws)}")
    else:
        r.add("考点权重=100", False, "缺考点文件")

    if run_log:
        from evaluation.blind_evaluation import admitted_runs, coverage_note
        runs = admitted_runs(run_log, p / "01_public/task_prompt.md")
        r.add("盲测运行记录", bool(runs), coverage_note(runs))

    meta = p / "00_meta.json"
    if meta.is_file():
        m = json.loads(meta.read_text(encoding="utf-8"))
        r.add("行业=金融", (m.get("industry_l1") or m.get("industry")) == "金融",
              str(m.get("industry_l1") or m.get("industry")))
        r.add("三级 Skill 已填", bool(m.get("level3_skill")), "")
        r.add("source_type 非空", bool(m.get("source_type")), "")
    else:
        r.add("00_meta.json", False, "缺失")

    return r
