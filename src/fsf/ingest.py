"""Material inventory: files, hashes, workbook/table structure, duplicates."""
from __future__ import annotations

from pathlib import Path

from .util import EXCEL_EXT, TEXT_EXT, human_bytes, iter_files, sha256_file, write_json


def _excel_meta(path: Path) -> dict:
    try:
        from openpyxl import load_workbook

        wb = load_workbook(path, read_only=True, data_only=True)
        sheets = [{"name": ws.title, "rows": ws.max_row or 0, "cols": ws.max_column or 0}
                  for ws in wb.worksheets]
        wb.close()
        return {"sheets": sheets}
    except ImportError:
        return {"sheets": [], "note": "openpyxl not installed"}
    except Exception as exc:  # noqa: BLE001
        return {"sheets": [], "error": f"{type(exc).__name__}: {exc}"}


def _text_meta(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8-sig", errors="strict") as f:
            lines = f.readlines()
        cols = max((len(ln.rstrip("\n").split(",")) for ln in lines[:50]), default=0)
        return {"rows": max(len(lines) - 1, 0), "cols_estimate": cols, "encoding": "utf-8"}
    except UnicodeDecodeError:
        return {"rows": None, "encoding": "not-utf8"}
    except Exception as exc:  # noqa: BLE001
        return {"rows": None, "error": f"{type(exc).__name__}: {exc}"}


def build_inventory(src: Path) -> dict:
    files = []
    for path in iter_files(src):
        rel = path.relative_to(src).as_posix()
        item = {"path": rel, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        ext = path.suffix.lower()
        if ext in EXCEL_EXT:
            item.update(_excel_meta(path))
        elif ext in TEXT_EXT:
            item.update(_text_meta(path))
        files.append(item)

    by_ext: dict[str, int] = {}
    for f in files:
        ext = Path(f["path"]).suffix.lower() or "(none)"
        by_ext[ext] = by_ext.get(ext, 0) + 1

    by_hash: dict[str, list[str]] = {}
    for f in files:
        by_hash.setdefault(f["sha256"], []).append(f["path"])
    duplicates = {h: ps for h, ps in by_hash.items() if len(ps) > 1}

    return {
        "source_dir": str(src.resolve()),
        "file_count": len(files),
        "total_bytes": sum(f["bytes"] for f in files),
        "by_ext": by_ext,
        "duplicates": duplicates,
        "files": files,
    }


def render_markdown(inv: dict) -> str:
    lines = [
        "# 材料盘点清单",
        "",
        f"- 源目录：`{inv['source_dir']}`",
        f"- 文件数：**{inv['file_count']}**；合计 {human_bytes(inv['total_bytes'])}",
        "- 类型分布：" + "、".join(f"{k}×{v}" for k, v in sorted(inv["by_ext"].items(), key=lambda x: -x[1])),
        f"- 重复文件组：**{len(inv['duplicates'])}**" + ("（见 JSON duplicates）" if inv["duplicates"] else ""),
        "",
        "| # | 文件 | 大小 | 结构 |",
        "|---:|---|---:|---|",
    ]
    for i, f in enumerate(inv["files"], 1):
        sheets = f.get("sheets") or []
        if sheets:
            shape = "；".join(f"{s['name']} {s['rows']}×{s['cols']}" for s in sheets[:4])
            if len(sheets) > 4:
                shape += f" …（{len(sheets)} sheet）"
        elif f.get("rows") is not None:
            shape = f"{f['rows']} 行 × ~{f.get('cols_estimate', '?')} 列"
        else:
            shape = f.get("error") or f.get("encoding") or (Path(f["path"]).suffix.lower() or "—")
        lines.append(f"| {i} | `{f['path']}` | {human_bytes(f['bytes'])} | {shape} |")
    return "\n".join(lines) + "\n"


def run_ingest(src: Path, out: Path) -> dict:
    inv = build_inventory(src)
    write_json(out / "material-inventory.json", inv)
    (out / "material-inventory.md").write_text(render_markdown(inv), encoding="utf-8")
    return inv
