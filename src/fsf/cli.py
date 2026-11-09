"""Command line entry point: python -m fsf {ingest,scan,check,pack}."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ingest import run_ingest
from .pack import pack_case
from .scan import run_scan


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fsf", description="Financial Skill Factory CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ingest", help="盘点案例材料")
    p.add_argument("case", type=Path)
    p.add_argument("--out", type=Path, required=True)

    p = sub.add_parser("scan", help="材料体检并出报告")
    p.add_argument("case", type=Path)
    p.add_argument("--out", type=Path, required=True)

    p = sub.add_parser("check", help="材料体检，FAIL 时非零退出")
    p.add_argument("case", type=Path)

    p = sub.add_parser("pack", help="生成六类材料骨架")
    p.add_argument("case", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--platform-id", default=None)
    p.add_argument("--task-name", default=None)

    ns = ap.parse_args(argv)

    if ns.cmd == "ingest":
        inv = run_ingest(ns.case / "materials", ns.out)
        print(f"files={inv['file_count']} bytes={inv['total_bytes']} dup_groups={len(inv['duplicates'])}")
        print(f"wrote {ns.out/'material-inventory.json'}")
        return 0

    if ns.cmd == "scan":
        rep = run_scan(ns.case, ns.out)
        print(f"verdict={rep['verdict']} fails={rep['fails']} warns={rep['warns']}")
        print(f"wrote {ns.out/'scan-report.md'}")
        return 0

    if ns.cmd == "check":
        case_dir = ns.case
        if not (case_dir / "case.yaml").is_file() and not (case_dir / "case.json").is_file():
            print(f"missing case.yaml in {case_dir}", file=sys.stderr)
            return 2
        out = Path("out") / case_dir.name
        rep = run_scan(case_dir, out)
        print(f"verdict={rep['verdict']} fails={rep['fails']} warns={rep['warns']}")
        return 1 if rep["fails"] else 0

    if ns.cmd == "pack":
        pack_dir = pack_case(ns.case, ns.out, ns.platform_id, ns.task_name)
        print(f"packed -> {pack_dir}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
