import importlib.util
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_engine():
    spec = importlib.util.spec_from_file_location("candidate", ROOT / "12_现行引擎.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    result = load_engine().compile_settlement(ROOT, "CLOSE", None)
    assert {r["instruction_id"] for r in result["report"]} >= {"I01", "I02"}
    for row in result["report"]:
        Decimal(row["settled_quantity"])
        Decimal(row["open_quantity"])
        assert row["evidence_ids"] == sorted(set(row["evidence_ids"]))
    assert result["state"]["last_cutoff"] == "CLOSE"
    print("basic checks passed")


if __name__ == "__main__":
    main()
