from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--cut", required=True, choices=["OPEN", "MID", "CLOSE"])
    parser.add_argument("--prior-state")
    args = parser.parse_args()
    base = Path(args.input)
    spec = importlib.util.spec_from_file_location("engine", base / "12_现行引擎.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    prior = None
    if args.prior_state:
        prior = json.loads(Path(args.prior_state).read_text(encoding="utf-8"))
    print(json.dumps(mod.run(base, args.cut, prior), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
