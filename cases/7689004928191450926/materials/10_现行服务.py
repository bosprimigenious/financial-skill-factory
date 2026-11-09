from __future__ import annotations

import json
from pathlib import Path


def close(input_dir: Path, output_dir: Path) -> None:
    """现行版本只读取参数，尚未实现事件恢复、条款核验和封板。"""
    params = json.loads((input_dir / "02_运行参数.json").read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run_manifest.json").write_text(
        json.dumps({"company": params["company"], "status": "NOT_IMPLEMENTED"}, ensure_ascii=False),
        encoding="utf-8",
    )

