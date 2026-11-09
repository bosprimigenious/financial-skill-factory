"""Stage 5 · 盲测记录层。

V2 不假装能替你跑豆包。本模块负责：把"哪一次运行、跑的是哪个版本的题面、
用的是什么产品环境、结果如何"变成可核验的记录；并提供准入校验。

规则（缺一条即记录不合格）：
  1. 必须绑定题面哈希（返修后旧记录不得混算）
  2. status 必须是 COMPLETED / TIMEOUT / ABORTED_BY_HUMAN（ENV_FAILURE 无效）
  3. 运行期间不得人工纠错/辅导
  4. 保留全部运行，不允许只挑最低分
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from .difficulty_preflight import RunRecord


class InvalidRun(RuntimeError):
    pass


def prompt_hash(prompt_path: str | Path) -> str:
    return hashlib.sha256(Path(prompt_path).read_bytes()).hexdigest()


def make_run(*, run_id: str, task_id: str, prompt_path: str | Path, model: str, mode: str,
             judge_score: float, steps: int | None, seconds: float | None,
             status: str = "COMPLETED", human_intervention: bool = False,
             notes: str = "") -> RunRecord:
    if human_intervention:
        raise InvalidRun("运行期间出现人工纠错/辅导：该次不得作为难度证据")
    rec = RunRecord(run_id, task_id, prompt_hash(prompt_path), model, mode,
                    judge_score, steps, seconds, status, notes)
    rec.validate()
    return rec


def append(log_path: str | Path, rec: RunRecord) -> None:
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")


def load_all(log_path: str | Path) -> list[RunRecord]:
    p = Path(log_path)
    if not p.is_file():
        return []
    return [RunRecord(**json.loads(l)) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def admitted_runs(log_path: str | Path, prompt_path: str | Path) -> list[RunRecord]:
    """只认与当前题面版本绑定、且状态有效的运行。"""
    h = prompt_hash(prompt_path)
    out = []
    for r in load_all(log_path):
        if r.prompt_sha256 != h:
            continue
        if r.status == "ENV_FAILURE":
            continue
        out.append(r)
    return out


def coverage_note(runs: list[RunRecord]) -> str:
    if not runs:
        return "UNTESTED：无与当前题面绑定的有效运行"
    if len(runs) < 2:
        return f"仅 {len(runs)} 次有效运行：非确定性未观察，结论只代表该次"
    return f"{len(runs)} 次有效运行；不得只挑最低分，须报告全部"
