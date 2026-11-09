"""Shared helpers for the Financial Skill Factory."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

SKIP_NAMES = {".DS_Store", "Thumbs.db"}
TEXT_EXT = {".csv", ".tsv", ".txt", ".md", ".json"}
EXCEL_EXT = {".xlsx", ".xlsm"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    """Yield visible files under root in a stable order."""
    if not root.is_dir():
        raise FileNotFoundError(f"not a directory: {root}")
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name in SKIP_NAMES or name.startswith("."):
                continue
            yield Path(dirpath) / name


def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} GB"


def parse_minimal_yaml(text: str) -> dict:
    """Parse the small YAML subset used by case.yaml.

    Supported: top-level scalars, lists of scalars, lists of flat mappings.
    Unknown syntax raises ValueError instead of silently guessing.
    """
    root: dict = {}
    # stack of (indent, container, current_key_for_list)
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]

    def scalar(v: str) -> Any:
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            return v[1:-1]
        if v.startswith("'") and v.endswith("'"):
            return v[1:-1]
        low = v.lower()
        if low in ("true", "false"):
            return low == "true"
        if low in ("null", "~"):
            return None
        try:
            if "." in v:
                return float(v)
            return int(v)
        except ValueError:
            return v

    i = 0
    current_list_key: str | None = None
    while i < len(lines):
        raw = lines[i]
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            if ":" not in line:
                raise ValueError(f"bad line: {raw}")
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest:
                root[key] = scalar(rest)
                current_list_key = None
            else:
                root[key] = []
                current_list_key = key
            i += 1
            continue
        if current_list_key is None:
            raise ValueError(f"unexpected indented line: {raw}")
        if line.startswith("- "):
            item = line[2:].strip()
            container = root[current_list_key]
            if ":" in item:
                k, _, v = item.partition(":")
                entry = {k.strip(): scalar(v)} if v.strip() else {k.strip(): None}
                container.append(entry)
            else:
                container.append(scalar(item))
            i += 1
            continue
        # continuation key of the last mapping item
        if ":" not in line:
            raise ValueError(f"bad indented line: {raw}")
        k, _, v = line.partition(":")
        last = root[current_list_key][-1]
        if not isinstance(last, dict):
            raise ValueError(f"expected mapping item before: {raw}")
        last[k.strip()] = scalar(v)
        i += 1
    return root


def load_case(case_dir: Path) -> dict:
    yml = case_dir / "case.yaml"
    js = case_dir / "case.json"
    if yml.is_file():
        data = parse_minimal_yaml(yml.read_text(encoding="utf-8"))
    elif js.is_file():
        data = json.loads(js.read_text(encoding="utf-8"))
    else:
        raise FileNotFoundError(f"missing case.yaml/case.json in {case_dir}")
    data.setdefault("id", case_dir.name)
    data.setdefault("source_type", "unknown")
    data.setdefault("required_files", [])
    data.setdefault("checks", [])
    return data
