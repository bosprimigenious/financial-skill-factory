#!/usr/bin/env python3
"""一条命令跑产线：intake → 真实性 → 技能匹配 → 考点 → QA → 变异 → 难度 → 门禁。

存在的理由：V2 的八个模块散在各自目录里，靠人记顺序必然漏步。
这里把它们串成一次运行，并把每一步的 SKIP 原因写清楚——**跳过也要留痕**。

用法：
  python3 tools/fsf_run.py --all
  python3 tools/fsf_run.py --case cases/7689005313907642138
  python3 tools/fsf_run.py --all --out artifacts/pipeline-state.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from case_intake import authenticity_gate, source_registry          # noqa: E402
from evaluation import difficulty_preflight, mutation_test, rubric_qa  # noqa: E402
from generators import rubric_builder                             # noqa: E402
from quality_gates import xpert_readiness                         # noqa: E402
from task_architect import skill_mapper                           # noqa: E402

STAGES = ("intake", "authenticity", "skill", "rubric", "qa", "mutation", "difficulty", "readiness")


def _prompt_of(case: Path) -> str:
    for p in (case / "01_public/task_prompt.md", ROOT / "packs" / case.name / "01_public/task_prompt.md"):
        if p.is_file():
            return p.read_text(encoding="utf-8")
    return ""


def _fields(case: Path) -> dict:
    out = {}
    for base in (case / "materials", ROOT / "packs" / case.name / "01_public/data"):
        if not base.is_dir():
            continue
        for f in sorted(base.glob("*.csv")):
            head = f.read_text(encoding="utf-8-sig").splitlines()[0]
            out[f.name] = [c.strip() for c in head.split(",")][:8]
        if out:
            break
    return out


def run_case(case: Path, occupied: set[str], want: dict) -> dict:
    rec: dict = {"case": case.name, "stages": {}}

    # ---- Stage 0 intake ----
    src = None
    try:
        src = source_registry.CaseSource.load(case)
        source_registry.CaseSource.verify_hashes(case, src)
        rec["stages"]["intake"] = ("OK", f"{len(src.materials)} 件材料，哈希一致")
    except FileNotFoundError:
        rec["stages"]["intake"] = ("SKIP", "未登记（source_registry.json 不存在）")
    except source_registry.MaterialChanged as e:
        rec["stages"]["intake"] = ("FAIL", str(e)[:120])

    meta = json.loads((case / "case.json").read_text(encoding="utf-8")) if (case / "case.json").is_file() else {}
    prompt = _prompt_of(case)

    # ---- Stage 0 authenticity ----
    if src is None:
        rec["stages"]["authenticity"] = ("SKIP", "缺登记，无法判定")
    else:
        g = authenticity_gate.check(src=src, prompt_text=prompt or "匿名",
                                    materials_text="", occupied_skills=occupied,
                                    level3_skill=src.level3_skill or meta.get("level3_skill_proposed", ""))
        rec["stages"]["authenticity"] = ("OK" if g.passed else "FAIL",
                                         "; ".join(f"{r}:{m}" for r, m in g.failures) or "7 条全过")

    # ---- Stage 1 skill ----
    title = meta.get("title") or case.name
    proposed = (meta.get("level3_skill_proposed") or "").strip()
    if proposed and proposed not in ("待平台词条确认", "TBD"):
        # 登记里已声明三级 Skill 时以登记为准；映射器结果降为参考
        rec["stages"]["skill"] = ("OK", f"登记：{proposed}（映射器仅参考）")
        return _finish(rec, case, occupied, want, prompt, meta)
    try:
        cands = skill_mapper.map_task(title, ROOT / "registry/financial_domains.yaml", occupied=occupied)
        best = skill_mapper.require_unique(cands) if cands else None
        rec["stages"]["skill"] = ("OK", f"{best.l2} / {best.l3}" if best else "无候选") if best \
            else ("FAIL", "无可用候选（均被占用）")
    except Exception as e:                                   # noqa: BLE001
        rec["stages"]["skill"] = ("FAIL", str(e)[:120])

    return _finish(rec, case, occupied, want, prompt, meta)


def _finish(rec: dict, case: Path, occupied: set[str], want: dict,
            prompt: str, meta: dict) -> dict:
    # ---- Stage 3D rubric ----
    fields = _fields(case)
    rub = None
    if not prompt or not fields:
        rec["stages"]["rubric"] = ("SKIP", "缺题面或材料字段")
    else:
        try:
            rub = rubric_builder.build(task_id=case.name, prompt=prompt, materials_fields=fields)
            rec["stages"]["rubric"] = ("OK", f"{len(rub.items)} 条 / 合计 {rub.total}")
        except Exception as e:                               # noqa: BLE001
            rec["stages"]["rubric"] = ("FAIL", str(e)[:120])

    # ---- Stage 4.5 QA ----
    if rub is None:
        rec["stages"]["qa"] = ("SKIP", "无考点")
    else:
        qa = rubric_qa.run_all(rub, prompt)
        rec["stages"]["qa"] = ("OK" if qa["ok"] else "FAIL", f"fail={qa['fail']} warn={qa['warn']}")

    # ---- Stage 4.6 mutation ----
    expected_path = case / "mutation_expected.json"
    if not expected_path.is_file():
        rec["stages"]["mutation"] = ("SKIP", "缺 mutation_expected.json")
    else:
        spec = json.loads(expected_path.read_text(encoding="utf-8"))
        res = mutation_test.run({k: tuple(v) for k, v in spec["expected"].items()}, spec["weights"])
        s = mutation_test.summarise(res)
        rec["stages"]["mutation"] = ("OK" if s["ok"] else "FAIL", f"{s['total'] - s['failed']}/{s['total']}")

    # ---- Stage 5.5 difficulty ----
    log = case / "04_evidence/runs.jsonl"
    if not log.is_file():
        rec["stages"]["difficulty"] = ("SKIP", "无运行记录（UNTESTED，不得当作达标）")
    else:
        runs = difficulty_preflight_run(log, case, want)
        rec["stages"]["difficulty"] = runs

    # ---- Stage 6 readiness ----
    pack = ROOT / "packs" / case.name
    if not pack.is_dir():
        rec["stages"]["readiness"] = ("SKIP", "尚未生成题包")
    else:
        r = xpert_readiness.evaluate(pack)
        rec["stages"]["readiness"] = ("OK" if r.ready else "FAIL", f"{len(r.blockers)} 个 blocker")
    return rec


def difficulty_preflight_run(log: Path, case: Path, want: dict) -> tuple[str, str]:
    rule = difficulty_preflight.load_rule(ROOT / "registry/difficulty_rule.yaml")
    runs = [difficulty_preflight.RunRecord(**json.loads(l))
            for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not runs:
        return ("SKIP", "运行记录为空")
    out = [difficulty_preflight.preflight(r, rule) for r in runs]
    verd = [o["verdict"] for o in out]
    return ("OK" if "PASS" in verd else "FAIL",
            f"{len(runs)} 次运行，PASS {verd.count('PASS')} / FAIL {verd.count('FAIL')}，"
            f"读法 {rule.get('combine')}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", action="append", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default="artifacts/pipeline-state.md")
    a = ap.parse_args()

    occupied = authenticity_gate.occupied_from(ROOT / "registry/submitted_skill_registry.json")
    want = {"combine": "all"}

    if a.all:
        targets = sorted(d for d in (ROOT / "cases").iterdir()
                         if d.is_dir() and (d / "case.json").is_file())
    elif a.case:
        targets = [Path(c) if Path(c).is_absolute() else ROOT / c for c in a.case]
        bad = [t for t in targets if not t.is_dir()]
        if bad:
            print(f"case 不存在：{bad}", file=sys.stderr)
            return 2
    else:
        ap.error("需要 --case 或 --all")

    rows = [run_case(t, occupied, want) for t in targets]

    lines = ["# 产线状态（tools/fsf_run.py 现场生成）", "",
             f"- 运行范围：{len(rows)} 个案例",
             f"- 占用集：{len(occupied)} 个三级 Skill",
             "",
             "| 案例 | intake | authenticity | skill | rubric | qa | mutation | difficulty | readiness |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        cells = []
        for s in STAGES:
            st, detail = r["stages"].get(s, ("SKIP", "未执行"))
            cells.append(f"{st}" if st == "OK" else f"**{st}**")
        lines.append(f"| `{r['case']}` | " + " | ".join(cells) + " |")
    lines += ["", "## 明细", ""]
    for r in rows:
        lines.append(f"### {r['case']}")
        for s in STAGES:
            st, detail = r["stages"].get(s, ("SKIP", "未执行"))
            lines.append(f"- **{s}** {st} — {detail}")
        lines.append("")

    out = Path(a.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:10]))
    print(f"\nwrote {out}")
    fails = sum(1 for r in rows for st, _ in r["stages"].values() if st == "FAIL")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
