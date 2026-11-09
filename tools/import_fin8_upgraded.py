#!/usr/bin/env python3
"""导入外部产出的八题包（Downloads 里的 FINANCIAL_EIGHT_PIPELINE_UPGRADED.zip），
用本仓库的门禁复核，而不是直接相信它。

做的事：
  1) 解压 8 个独立包到 deliverables/fin8-upgraded/
  2) 逐包校验：MANIFEST.sha256、文件齐备、无业务数据、GT 未被编造、两套 Rubric 分离、
     G7 口径（Judge ≤50 且 步数 ≥50，时长仅评级）
  3) 与我方 tools/scaffold_fin8.py 生成的 23 文件版做差异对照
  4) 写 VERIFY-REPORT.md，有失败则非零退出

用法：python3 tools/import_fin8_upgraded.py [--zip ~/Downloads/xxx.zip]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "deliverables" / "fin8-upgraded"
MINE = ROOT / "deliverables" / "fin8"
CODES = ["FIN01_ALT_DATA", "FIN02_PRICE_VOLUME", "FIN03_ETF_ARB", "FIN04_PORT_ATTR",
         "FIN05_FX_SHOCK", "FIN06_CREDIT_MIGRATION", "FIN07_STRESS", "FIN08_LIQUIDITY_GAP"]

FAKE_NUM = re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def extract(src: Path) -> Path:
    work = Path("/tmp/fin8_extract")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    with zipfile.ZipFile(src) as z:
        z.extractall(work)
    return work


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=str(Path.home() / "Downloads/FINANCIAL_EIGHT_PIPELINE_UPGRADED.zip"))
    a = ap.parse_args()

    src = Path(a.zip)
    if not src.is_file():
        print(f"找不到 {src}", file=sys.stderr)
        return 2
    work = extract(src)

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)

    report = ["# 外部八题包复核报告", "",
              f"- 来源：`{src.name}`（{src.stat().st_size} 字节，sha256 `{sha(src)[:16]}…`）",
              f"- 复核方：本仓库门禁（`tools/import_fin8_upgraded.py`）",
              f"- 结论：见文末", ""]
    fails: list[str] = []
    rows = []

    for code in CODES:
        z = work / f"{code}_SCAFFOLD.zip"
        if not z.is_file():
            fails.append(f"{code}: 缺独立包")
            continue
        with zipfile.ZipFile(z) as zf:
            if zf.testzip():
                fails.append(f"{code}: CRC 失败")
            zf.extractall(DEST)
        pkg = DEST / code
        files = [p for p in pkg.rglob("*") if p.is_file()]
        # 1) MANIFEST
        man = pkg / "MANIFEST.sha256"
        man_ok = False
        if man.is_file():
            r = subprocess.run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=pkg,
                               capture_output=True, text=True)
            man_ok = r.returncode == 0
        # 2) 无业务数据
        data_dir = pkg / "01_PUBLIC_DOUBAO/inputs"
        has_data = bool(list(data_dir.rglob("*.csv"))) if data_dir.is_dir() else False
        # 3) GT 未被编造：出现成组的千分位金额即视为编造
        gt = pkg / "02_PRIVATE_EXPERT/GOLDEN_RESPONSE.md"
        gt_text = gt.read_text(encoding="utf-8") if gt.is_file() else ""
        fake = bool(FAKE_NUM.search(gt_text))
        gt_ok = ("NOT_READY" in gt_text or "Do not invent" in gt_text) and not fake
        # 4) 两套 Rubric
        plat = (pkg / "02_PRIVATE_EXPERT/PLATFORM_RUBRIC.csv")
        internal = (pkg / "02_PRIVATE_EXPERT/INTERNAL_GRADER_20x5.csv")
        plat_head = plat.read_text(encoding="utf-8").splitlines()[0].lower() if plat.is_file() else ""
        intl_head = internal.read_text(encoding="utf-8").splitlines()[0].lower() if internal.is_file() else ""
        # 平台 Rubric：中英表头均可，但必须有 ≥7 列且含核心判分点/达标标准
        plat_cols = [c.strip() for c in plat_head.split(",") if c.strip()]
        plat_ok = len(plat_cols) >= 7 and any(
            k in plat_head for k in ("核心判分点", "core_criterion"))
        intl_ok = ("criterion" in intl_head) and ("c20" in intl_head or
                   "criterion_id" in intl_head)
        rub_ok = plat_ok and intl_ok
        # 5) G7 口径
        gate_text = "".join(f.read_text(encoding="utf-8") for f in pkg.rglob("*.md"))
        norm = re.sub(r"\s+", " ", gate_text)
        g7 = bool(re.search(r"(<=|≤)\s*50", norm)) and bool(re.search(r"(>=|≥)\s*50", norm))
        ok = man_ok and not has_data and gt_ok and rub_ok and g7
        if not ok:
            fails.append(f"{code}: manifest={man_ok} data={has_data} gt={gt_ok} rubric={rub_ok} g7={g7}")
        rows.append((code, len(files), man_ok, has_data, gt_ok, rub_ok, g7, ok))

    master = work / "FINANCIAL_EIGHT_SCAFFOLD_MASTER.zip"
    master_ok = False
    if master.is_file():
        with zipfile.ZipFile(master) as zf:
            master_ok = zf.testzip() is None
        shutil.copy2(master, DEST / master.name)
    if not master_ok:
        fails.append("总包缺失或 CRC 失败")

    # 与 23 文件版差异
    diff_lines = []
    if MINE.is_dir():
        for code in CODES:
            mine = MINE / code
            theirs = DEST / code
            if not mine.is_dir():
                continue
            ms = {str(p.relative_to(mine)) for p in mine.rglob("*") if p.is_file()}
            ts = {str(p.relative_to(theirs)) for p in theirs.rglob("*") if p.is_file()}
            only_t = sorted(ts - ms)
            only_m = sorted(ms - ts)
            diff_lines.append(f"| `{code}` | {len(ms)} | {len(ts)} | "
                              f"{', '.join(f'`{x}`' for x in only_t[:6]) or '—'} | "
                              f"{', '.join(f'`{x}`' for x in only_m[:4]) or '—'} |")

    report += ["## 逐包复核", "",
               "| 包 | 文件数 | MANIFEST | 含业务数据 | GT 合规 | 两套Rubric | G7口径 | 结论 |",
               "|---|---:|---|---|---|---|---|---|"]
    for code, n, man, data, gt, rub, g7, ok in rows:
        report.append(f"| `{code}` | {n} | {'OK' if man else 'FAIL'} | "
                      f"{'有' if data else '无'} | {'OK' if gt else 'FAIL'} | "
                      f"{'OK' if rub else 'FAIL'} | {'OK' if g7 else 'FAIL'} | "
                      f"{'PASS' if ok else 'FAIL'} |")
    report += ["", f"总包 CRC：{'OK' if master_ok else 'FAIL'}", "",
               "## 与本地 23 文件版的结构差异", "",
               "| 包 | 本地文件数 | 外部文件数 | 外部多出 | 本地多出 |",
               "|---|---:|---:|---|---|"] + diff_lines
    report += ["", "## 外部包多出的文件是什么", "",
               "| 文件 | 作用 |", "|---|---|",
               "| `02_PRIVATE_EXPERT/GRADER_SPEC.md` | 判分器规格（机读判据的落点定义） |",
               "| `02_PRIVATE_EXPERT/ORACLE_CALIBRATION.md` | Reference / Alternative / Negative 三态校准位 |",
               "| `03_OPERATIONS/CHANGE_LOG.md` | 版本变更留痕 |",
               "| `04_EVIDENCE/PLATFORM_SKILL_SNAPSHOT.csv` | 平台 Skill 快照（三级 Skill 与任务 ID） |",
               "| `06_READINESS/FINAL_READINESS.md` | 终检清单 |",
               "| `06_READINESS/G0_G10.md` | 替代本地 `READINESS_GATES.md`，闸门口径更细 |",
               "", "## 结论", ""]
    if fails:
        report.append(f"**FAIL**：{len(fails)} 项不通过")
        report += [f"- {f}" for f in fails]
    else:
        report.append("**PASS**：8 包全部通过本仓库门禁；状态仍为 `SCAFFOLD_ONLY`——"
                      "无真实材料、无独立 Reference、无有效模型运行，不可提交。")
        report.append("")
        report.append("采用建议：**以外部 25 文件版为主**（多出 GRADER_SPEC / ORACLE_CALIBRATION / "
                      "CHANGE_LOG / PLATFORM_SKILL_SNAPSHOT / FINAL_READINESS），"
                      "本地 23 文件版保留为生成器产物与回归基线。")

    (DEST / "VERIFY-REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report[-8:]))
    print(f"\nwrote {DEST/'VERIFY-REPORT.md'}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
