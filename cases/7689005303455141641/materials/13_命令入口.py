import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path


def load_engine(path):
    spec = importlib.util.spec_from_file_location("settlement_engine", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--cutoff", required=True)
    p.add_argument("--state", type=Path)
    a = p.parse_args()
    prior = json.loads(a.state.read_text(encoding="utf-8")) if a.state else None
    engine = load_engine(a.input / "12_现行引擎.py")
    result = engine.compile_settlement(a.input, a.cutoff, prior)
    a.output.mkdir(parents=True, exist_ok=True)

    def write_jsonl(name, rows):
        data = "".join(json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for x in rows).encode("utf-8")
        (a.output / name).write_bytes(data)
        return data

    report = write_jsonl("settlement_report.jsonl", result["report"])
    plan = write_jsonl("settlement_plan.jsonl", result.get("plan", []))
    actions = write_jsonl("remediation_actions.jsonl", result["actions"])
    rec_path = a.output / "position_reconciliation.csv"
    fields = ["account", "isin", "custody_account", "expected_quantity", "custody_quantity", "difference", "status", "evidence_ids"]
    with rec_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in result["reconciliation"]:
            w.writerow(row)
    state_data = (json.dumps(result["state"], ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    (a.output / "state.json").write_bytes(state_data)
    output_parts = []
    for name in sorted(["settlement_report.jsonl", "settlement_plan.jsonl", "remediation_actions.jsonl", "position_reconciliation.csv"]):
        output_parts.append((a.output / name).read_bytes())
    manifest = {
        "cutoff_id": a.cutoff,
        "report_count": len(result["report"]),
        "plan_count": len(result.get("plan", [])),
        "action_count": len(result["actions"]),
        "reconciliation_count": len(result["reconciliation"]),
        "input_digest": input_digest(a.input),
        "output_digest": hashlib.sha256(b"".join(output_parts)).hexdigest(),
    }
    (a.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def input_digest(folder):
    h = hashlib.sha256()
    for path in sorted([p for p in folder.iterdir() if p.name[:2].isdigit() and p.suffix in {".jsonl", ".json", ".csv", ".md", ".py"}], key=lambda p: p.name):
        lines = [line for line in path.read_bytes().splitlines(keepends=True) if line.strip()]
        for line in sorted(lines):
            h.update(line.replace(b"\r\n", b"\n"))
    return h.hexdigest()


if __name__ == "__main__":
    main()
