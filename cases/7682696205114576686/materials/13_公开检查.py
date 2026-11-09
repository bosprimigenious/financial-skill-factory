from __future__ import annotations

import importlib.util
import json
import random
import shutil
from pathlib import Path


BASE = Path(__file__).parent


def load(path: Path):
    spec = importlib.util.spec_from_file_location("candidate", path / "12_现行引擎.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main():
    mod = load(BASE)
    close = mod.run(BASE, "CLOSE", None)
    assert set(close) == {"order_control", "allocation_fees", "correction_journal", "state"}
    assert close["state"]["schema_version"] == 1
    assert close["state"]["cut_id"] == "CLOSE"
    assert canonical(close) == canonical(mod.run(BASE, "CLOSE", close["state"]))
    for key in ["order_control", "allocation_fees", "correction_journal"]:
        assert isinstance(close[key], list)
    work = BASE / ".public_check_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    try:
        for p in BASE.iterdir():
            if p.is_file():
                shutil.copy2(p, work / p.name)
        for name in ["05_批次账本.jsonl", "07_订单事件.jsonl", "08_成交事件.jsonl", "09_分配事件.jsonl"]:
            p = work / name
            lines = p.read_text(encoding="utf-8").splitlines()
            random.Random(76686).shuffle(lines)
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        assert canonical(close) == canonical(load(work).run(work, "CLOSE", None))
    finally:
        shutil.rmtree(work)
    print("public checks passed")


if __name__ == "__main__":
    main()
