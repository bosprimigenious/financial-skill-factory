"""Stage 5.5 · 二轮难度预检。

门槛是**配置**（`registry/difficulty_rule.yaml`），不是常量。
两种读法同时输出：

  A. any_two：judge<=50 且（steps>=50 或 time>2400s）   ← 仓库现行书面口径
  B. all    ：judge<=50 且 steps>=50                    ← 改造建议里的陈述

预检不替项目方选边：把两条结论都写进记录，争议时可复现"当时按哪条判的"。
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

STATUS = ("COMPLETED", "TIMEOUT", "ABORTED_BY_HUMAN", "ENV_FAILURE")


@dataclass
class RunRecord:
    run_id: str
    task_id: str
    prompt_sha256: str          # 与题面版本绑定：返修后旧记录不得混算
    model: str
    mode: str
    judge_score: float
    steps: int | None = None
    seconds: float | None = None
    status: str = "COMPLETED"
    notes: str = ""

    def validate(self) -> None:
        if self.status not in STATUS:
            raise ValueError(f"status 必须是 {STATUS}")
        if self.status == "ENV_FAILURE":
            raise ValueError("环境故障不得作为难度证据（记录为无效运行）")
        if not self.prompt_sha256:
            raise ValueError("缺少题面哈希：无法确认与哪个版本绑定")


def load_rule(path: str | Path) -> dict:
    d: dict = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or ":" not in s:
            continue
        k, _, v = s.partition(":")
        v = v.split("#")[0].strip()
        try:
            d[k.strip()] = int(v) if v.lstrip("-").isdigit() else float(v) if v.replace(".", "").isdigit() else v
        except ValueError:
            d[k.strip()] = v
    return d


def preflight(rec: RunRecord, rule: dict) -> dict:
    rec.validate()
    jmax = float(rule.get("judge_max", 50))
    smin = int(rule.get("steps_min", 50))
    tmin = int(rule.get("time_min_seconds", 2400))

    judge_ok = rec.judge_score <= jmax
    steps_known = rec.steps is not None
    time_known = rec.seconds is not None
    steps_ok = (rec.steps or 0) >= smin if steps_known else None
    time_ok = (rec.seconds or 0) > tmin if time_known else None

    def combine(mode: str):
        if mode == "all":
            return judge_ok and bool(steps_ok)
        if mode == "any":
            return judge_ok and (bool(steps_ok) or bool(time_ok))
        # any_two：步数或时长满足其一
        return judge_ok and (bool(steps_ok) or bool(time_ok))

    readings = {"any_two": combine("any_two"), "all": combine("all")}
    chosen = rule.get("combine", "any_two")
    return {
        "run": asdict(rec),
        "rule": rule,
        "judge_ok": judge_ok,
        "steps_ok": steps_ok, "time_ok": time_ok,
        "unverifiable": [k for k, v in (("steps", steps_ok), ("time", time_ok)) if v is None],
        "readings": readings,
        "verdict": "PASS" if readings.get(chosen) else "FAIL",
        "verdict_by_reading": {k: ("PASS" if v else "FAIL") for k, v in readings.items()},
        "chosen_reading": chosen,
        "note": ("步数/时长无记录时标 UNVERIFIABLE，不得用其他量替代" if
                 (steps_ok is None or time_ok is None) else ""),
    }
