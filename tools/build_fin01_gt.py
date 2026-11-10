#!/usr/bin/env python3
"""FIN01 的 Calculation GT：只从 materials/ 算，不猜数。

输出 packs/fin01/gt_table.csv + 覆盖/滞后/前视三项结论，供 GT 文本引用。

用法：python3 tools/build_fin01_gt.py
"""
from __future__ import annotations

import csv
import json
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=8))

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT / "packs/fin01/materials"


def read(name: str) -> list[dict]:
    with (MAT / name).open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_dt(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    # 统一按 Asia/Shanghai 解释；无时区的按当地交易日处理
    if s.endswith("Z"):
        s = s[:-1] + "+0000"
    for fmt in ("%Y-%m-%dT%H:%M%z", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s.replace("+08:00", "+0800"), fmt)
        except ValueError:
            continue
        return dt if dt.tzinfo else dt.replace(tzinfo=TZ)
    return None


def main() -> int:
    m1, m2, m3 = read("M1_数据源目录.csv"), read("M2_观测数据.csv"), read("M3_实体映射.csv")

    # 目录声明的覆盖实体数：coverage_note 里写明条数
    declared = {}
    for s in m1:
        note = s["coverage_note"]
        n = 0
        for token in note.replace("+", " ").replace("，", " ").replace(",", " ").split():
            digits = "".join(ch for ch in token if ch.isdigit())
            if digits and ("条" in token or "个" in token):
                n += int(digits)
        declared[s["source_id"]] = n or 1

    # 逐源统计：观测实体数、可用值数、滞后、前视风险
    rows = []
    for sid in declared:
        obs = [r for r in m2 if r["source_id"] == sid]
        entities = {r["entity"] for r in obs}
        valued = [r for r in obs if (r["value"] or "").strip()]
        valued_entities = {r["entity"] for r in valued}
        missing_proven = [r for r in obs if not (r["value"] or "").strip()]
        lags = []
        for r in obs:
            ts, rel = parse_dt(r["ts"]), parse_dt(r["released_at"])
            if ts and rel:
                lags.append((rel - ts).total_seconds() / 86400)
        no_release = [r for r in obs if not (r["released_at"] or "").strip()]
        rows.append({
            "source_id": sid,
            "declared_entities": declared[sid],
            "observed_entities": len(valued_entities),
            "entities_seen_without_value": len(entities - valued_entities),
            "records": len(obs),
            "valued_records": len(valued),
            "not_proven_records": len(missing_proven),
            "coverage_ratio": round(len(valued_entities) / declared[sid], 4) if declared[sid] else None,
            "median_lag_days": round(statistics.median(lags), 4) if lags else None,
            "max_lag_days": round(max(lags), 4) if lags else None,
            "records_missing_released_at": len(no_release),
            "pit_verdict": ("PASS" if valued and not no_release and (not lags or max(lags) <= 1)
                            else "FAIL"),
        })

    out = ROOT / "packs/fin01/gt_table.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # 实体映射一致性
    mapped = {r["entity"] for r in m3}
    observed = {r["entity"] for r in m2}
    unmapped = sorted(observed - mapped)
    dup_code = {}
    for r in m3:
        dup_code.setdefault(r["ticker"], set()).add(r["exchange"])

    summary = {
        "sources": len(rows),
        "declared_entities_total": sum(r["declared_entities"] for r in rows),
        "observed_entities_total": sum(r["observed_entities"] for r in rows),
        "overall_coverage_ratio": round(
            sum(r["observed_entities"] for r in rows) / sum(r["declared_entities"] for r in rows), 4),
        "not_proven_records_total": sum(r["not_proven_records"] for r in rows),
        "records_missing_released_at_total": sum(r["records_missing_released_at"] for r in rows),
        "sources_failing_pit": [r["source_id"] for r in rows if r["pit_verdict"] == "FAIL"],
        "unmapped_entities": unmapped,
        "tickers_across_exchanges": {k: sorted(v) for k, v in dup_code.items() if len(v) > 1},
        "count_check": {
            "fields_total": len({(r["source_id"], r["entity"], r["field"]) for r in m2}),
            "fields_modeled": len({(r["source_id"], r["entity"], r["field"])
                                   for r in m2 if (r["value"] or "").strip()}),
            "fields_rejected": len({(r["source_id"], r["entity"], r["field"])
                                    for r in m2 if not (r["value"] or "").strip()}),
            "not_observed_sources": [r["source_id"] for r in rows
                                     if r["records"] == 0],
            "note": "入模字段 + 拒绝字段 = 字段总数，见 rubric 勾稽项",
        },
    }
    (ROOT / "packs/fin01/gt_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"gt_table.csv  源 {len(rows)} 条")
    for r in rows:
        print(f"  {r['source_id']}  覆盖 {r['observed_entities']}/{r['declared_entities']}"
              f"={r['coverage_ratio']}  滞后中位 {r['median_lag_days']}天  "
              f"NOT_PROVEN {r['not_proven_records']}  PIT={r['pit_verdict']}")
    print(f"整体覆盖率 {summary['overall_coverage_ratio']}；"
          f"未登记实体 {summary['unmapped_entities']}；"
          f"跨交易所同码 {summary['tickers_across_exchanges']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
