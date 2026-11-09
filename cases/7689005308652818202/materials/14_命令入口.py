from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python 14_命令入口.py BUNDLE_DIR CUTOFF", file=sys.stderr)
        return 2
    service_path = Path(__file__).with_name("13_现行服务.py")
    spec = importlib.util.spec_from_file_location("risk_close_submission", service_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    result = module.evaluate_bundle(sys.argv[1], sys.argv[2])
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

