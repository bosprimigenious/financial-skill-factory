from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


VERSION = "0.3.2"


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_rows(rows, key="logical_id"):
    # 现行逻辑依赖文件顺序，未处理业务截止、知识截止、撤回与修订并列。
    out = {}
    for row in rows:
        out[row[key]] = row
    return list(out.values())


def funnel(opportunities, events):
    # 现行逻辑把每条重试都计入分子，也没有核对阶段时限。
    counts = {}
    for opportunity in opportunities:
        segment = opportunity["segment"]
        counts.setdefault(segment, {"qualified": 0, "accepted": 0, "activated": 0})
        counts[segment]["qualified"] += 1
    for event in events:
        segment = event.get("segment", "UNKNOWN")
        if segment not in counts:
            continue
        if event.get("stage") == "ACCEPTED":
            counts[segment]["accepted"] += 1
        if event.get("stage") == "ACTIVATED":
            counts[segment]["activated"] += 1
    return counts


def choose_action(summary):
    # 现行逻辑用相关性和总收入排序，没有工具变量、利润或现金边界。
    actions = []
    for segment, values in sorted(summary.items()):
        rate = values["accepted"] / values["qualified"] if values["qualified"] else 0.0
        actions.append({
            "segment": segment,
            "fee_delta_bps": 4 if rate > 0.4 else -4,
            "term_delta_days": 0,
            "action": "CHANGE",
        })
    return actions


def run(input_dir: Path, output_dir: Path):
    opportunities = read_csv(input_dir / "02_机会与主体.csv")
    events = []
    with (input_dir / "05_漏斗事件.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            events.append(json.loads(line))
    summary = funnel(opportunities, events)
    actions = choose_action(summary)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "selected_actions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(actions[0]))
        writer.writeheader()
        writer.writerows(actions)
    (output_dir / "release_decision.json").write_text(
        json.dumps({"overall_decision": "PROCEED", "actions": actions}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--input-dir", required=True)
    run_parser.add_argument("--output-dir", required=True)
    run_parser.add_argument("--business-cutoff")
    run_parser.add_argument("--knowledge-cutoff")
    args = parser.parse_args()
    if args.command == "run":
        run(Path(args.input_dir), Path(args.output_dir))


if __name__ == "__main__":
    main()

