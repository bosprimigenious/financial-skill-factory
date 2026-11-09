#!/usr/bin/env python3
"""打包单题交付物：题包 + 豆包运行记录 + 平台提交稿 + MANIFEST。

缺什么就在 README 与 MANIFEST 里写明缺什么——**不把缺失包装成完成**。

用法：python3 tools/package_one.py --code fin01 --item 7705055555161788179
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))


def sha(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", default="fin01")
    ap.add_argument("--item", default="7705055555161788179")
    ap.add_argument("--out", default="deliverables")
    a = ap.parse_args()

    pack = ROOT / "packs" / a.code
    run = ROOT / "runs" / a.code
    out_dir = ROOT / a.out / a.code
    out_dir.mkdir(parents=True, exist_ok=True)

    has_run = (run / "doubao_run.json").is_file()
    run_rec = json.loads((run / "doubao_run.json").read_text(encoding="utf-8")) if has_run else None

    files: list[tuple[Path, str]] = []
    for p in sorted(pack.rglob("*")):
        if p.is_file():
            files.append((p, f"pack/{p.relative_to(pack)}"))
    if has_run:
        for p in sorted(run.rglob("*")):
            if p.is_file():
                files.append((p, f"run/{p.relative_to(run)}"))

    gaps = []
    if not (pack / "materials").is_dir() or not any((pack / "materials").iterdir()):
        gaps.append("材料未接入：packs/fin01/materials 为空（需真实公开数据，按 materials_contract.md 落盘）")
    if not has_run:
        gaps.append("豆包未运行：无 runs/fin01/doubao_run.json（CDP 9334 不可用）")
    if has_run and run_rec.get("status") != "COMPLETED":
        gaps.append(f"豆包运行未完成：status={run_rec.get('status')}")

    readme = ["# FIN01 交付包", "",
              f"- 题目ID：`{a.item}`",
              f"- 三级 Skill：查询行业高频与另类数据",
              f"- 生成时间：{datetime.now(TZ).isoformat(timespec='seconds')}",
              f"- 文件数：{len(files)}", "",
              "## 包含", "",
              "| 目录 | 内容 |", "|---|---|",
              "| `pack/` | 题面、Ideal Steps、Rubric、材料契约、GT 方法、状态 |",
              "| `run/` | 豆包运行记录（prompt 哈希、分享链接、回答全文、耗时） |" if has_run else "| `run/` | （本次缺） |",
              "", "## 缺口（未完成的部分）", ""]
    readme += [f"- {g}" for g in gaps] or ["- 无"]
    readme += ["", "## 平台填写状态", "",
               "| 区块 | 状态 |", "|---|---|",
               "| 专家信息 4 项 | 需本人填写（昵称/飞书/岗位/资质） |",
               "| 能力选择 | 待勾选：查询运价、开工率、排产、招投标、卫星与客流等高频另类数据并说明口径 |",
               "| 提示词 / Ideal Steps / Rubric | ✅ 见 pack/ |",
               "| GT | 待材料接入后按 gt.md 独立计算 |",
               "| 豆包输出 | ✅ 见 run/" if has_run else "| 豆包输出 | ❌ 未运行 |",
               "| 难度 / 评级 / 评价 | 待豆包运行后填写 |",
               "| 联网要求 | 建议选「否」（材料自足） |", ""]
    (out_dir / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    manifest = {"item_id": a.item, "code": a.code,
                "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
                "status": "BLOCKED" if gaps else "READY_FOR_PLATFORM",
                "gaps": gaps,
                "files": [{"path": rel, "sha256": sha(p), "bytes": p.stat().st_size}
                          for p, rel in files]}
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")

    zpath = out_dir / f"FIN01_PACKAGE.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p, rel in files:
            z.write(p, rel)
        z.write(out_dir / "README.md", "README.md")
        z.write(out_dir / "MANIFEST.json", "MANIFEST.json")
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None

    print(f"{manifest['status']}  {zpath.name}  {zpath.stat().st_size // 1024} KB  "
          f"files={len(files) + 2}")
    for g in gaps:
        print("  gap:", g)
    return 0 if not gaps else 1


if __name__ == "__main__":
    raise SystemExit(main())
