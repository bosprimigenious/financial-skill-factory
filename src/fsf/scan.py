"""Material scan: completeness, structure, duplicates, declared numeric checks."""
from __future__ import annotations

from pathlib import Path

from .ingest import build_inventory
from .util import EXCEL_EXT, TEXT_EXT, human_bytes, load_case, write_json

ALLOWED_EXT = EXCEL_EXT | TEXT_EXT | {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".zip"}
MAX_FILE_BYTES = 50 * 1024 * 1024


def _check_cell(path: Path, sheet: str, cell: str) -> float | None:
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet not in wb.sheetnames:
            raise KeyError(f"sheet not found: {sheet} (have {wb.sheetnames})")
        value = wb[sheet][cell].value
    finally:
        wb.close()
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("¥", "").strip())
    except ValueError:
        return None


def scan_case(case_dir: Path) -> dict:
    case = load_case(case_dir)
    materials = case_dir / "materials"
    materials.mkdir(exist_ok=True)
    inv = build_inventory(materials)
    by_path = {f["path"]: f for f in inv["files"]}
    findings: list[dict] = []

    def add(level: str, code: str, message: str, evidence: str = "") -> None:
        findings.append({"level": level, "code": code, "message": message, "evidence": evidence})

    # 1. required files
    for rel in case.get("required_files", []):
        rel = str(rel)
        p = Path(rel)
        if p.parts and p.parts[0] == "materials":
            p = case_dir / p
        else:
            p = materials / p
        if not p.exists():
            add("FAIL", "missing_required", f"缺少必需材料：{rel}")
    # 2. duplicates
    for sha, paths in inv["duplicates"].items():
        add("WARN", "duplicate_file", f"重复文件（{sha[:8]}）：" + "、".join(paths))
    # 3. extension / size
    for f in inv["files"]:
        ext = Path(f["path"]).suffix.lower()
        if ext and ext not in ALLOWED_EXT:
            add("WARN", "extension", f"非常用格式：{f['path']}（{ext}）")
        if f["bytes"] > MAX_FILE_BYTES:
            add("WARN", "big_file", f"单文件超过 50MB：{f['path']}（{human_bytes(f['bytes'])}）")
    # 4. workbook structure
    for f in inv["files"]:
        if not f.get("sheets") and Path(f["path"]).suffix.lower() in EXCEL_EXT:
            add("FAIL", "xlsx_unreadable", f"工作簿无法读取：{f['path']} {f.get('error', '')}")
            continue
        for s in f.get("sheets", []):
            if s["rows"] <= 1:
                add("WARN", "empty_sheet", f"空表或仅表头：{f['path']} / {s['name']}（{s['rows']} 行）")
    # 5. csv emptiness / encoding
    for f in inv["files"]:
        if Path(f["path"]).suffix.lower() in TEXT_EXT:
            if f.get("encoding") == "not-utf8":
                add("WARN", "encoding", f"非 UTF-8，需转码后再用：{f['path']}")
            elif f.get("rows") == 0:
                add("WARN", "empty_csv", f"表格无数据行：{f['path']}")
    # 6. declared checks
    for i, chk in enumerate(case.get("checks", []), 1):
        ctype = (chk or {}).get("type")
        name = chk.get("name") or f"check-{i}"
        if ctype == "xlsx_cell":
            rel, sheet, cell = chk.get("file"), chk.get("sheet"), chk.get("cell")
            expect, tol = chk.get("expect"), float(chk.get("tolerance", 0.01))
            p = case_dir / rel if not str(rel).startswith("materials/") else case_dir / rel
            if not p.exists():
                add("FAIL", "check_missing_file", f"[{name}] 文件不存在：{rel}")
                continue
            try:
                value = _check_cell(p, sheet, cell)
            except Exception as exc:  # noqa: BLE001
                add("FAIL", "check_error", f"[{name}] 读取失败：{type(exc).__name__}: {exc}")
                continue
            if value is None:
                add("FAIL", "check_none", f"[{name}] {sheet}!{cell} 无缓存值（工作簿可能未重算）")
            elif expect is None:
                add("PASS", "check_read", f"[{name}] {sheet}!{cell} = {value}")
            elif abs(value - float(expect)) <= tol:
                add("PASS", "check_ok", f"[{name}] {sheet}!{cell} = {value}（期望 {expect}±{tol}）")
            else:
                add("FAIL", "check_mismatch",
                    f"[{name}] {sheet}!{cell} = {value}，期望 {expect}±{tol}（差 {value - float(expect):+.2f}）",
                    evidence=f"{rel}:{sheet}!{cell}")
        elif ctype in ("csv_min_rows", "xlsx_sheet_min_rows"):
            rel = chk.get("file")
            p = case_dir / rel
            if not p.exists():
                add("FAIL", "check_missing_file", f"[{name}] 文件不存在：{rel}")
                continue
            minimum = int(chk.get("min_rows", 1))
            if ctype == "csv_min_rows":
                rows = by_path.get(rel, {}).get("rows") or 0
                label = f"{rel} 行数"
            else:
                sheet = chk.get("sheet")
                meta = next((s for s in by_path.get(rel, {}).get("sheets", []) if s["name"] == sheet), None)
                rows = (meta or {}).get("rows", 0)
                label = f"{rel} / {sheet} 行数"
            if rows >= minimum:
                add("PASS", "rows_ok", f"[{name}] {label} = {rows}（≥{minimum}）")
            else:
                add("FAIL", "rows_short", f"[{name}] {label} = {rows} < {minimum}")
        else:
            add("WARN", "check_unknown", f"[{name}] 未知检查类型：{ctype}")

    fails = sum(1 for f in findings if f["level"] == "FAIL")
    warns = sum(1 for f in findings if f["level"] == "WARN")
    return {
        "case": case.get("id"),
        "source_type": case.get("source_type"),
        "materials": {
            "file_count": inv["file_count"],
            "total_bytes": inv["total_bytes"],
            "by_ext": inv["by_ext"],
            "duplicates": len(inv["duplicates"]),
        },
        "verdict": "FAIL" if fails else ("WARN" if warns else "PASS"),
        "fails": fails,
        "warns": warns,
        "findings": findings,
    }


def render_markdown(report: dict) -> str:
    lines = [
        f"# 材料体检报告 · {report['case']}",
        "",
        f"- 来源类型：`{report['source_type']}`",
        f"- 材料：{report['materials']['file_count']} 个 / {human_bytes(report['materials']['total_bytes'])}；"
        f"重复 {report['materials']['duplicates']} 组",
        f"- 结论：**{report['verdict']}**（FAIL {report['fails']} / WARN {report['warns']}）",
        "",
        "| 级别 | 代码 | 说明 |",
        "|---|---|---|",
    ]
    for f in report["findings"]:
        msg = f["message"].replace("|", "\\|")
        lines.append(f"| {f['level']} | `{f['code']}` | {msg} |")
    if not report["findings"]:
        lines.append("| PASS | — | 未发现问题 |")
    lines += ["", "> FAIL 必须补齐材料或修正口径后才能进入打包；WARN 需人工判断是否可接受。"]
    return "\n".join(lines) + "\n"


def run_scan(case_dir: Path, out: Path) -> dict:
    report = scan_case(case_dir)
    write_json(out / "scan-report.json", report)
    (out / "scan-report.md").write_text(render_markdown(report), encoding="utf-8")
    return report
