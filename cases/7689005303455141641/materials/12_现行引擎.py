import hashlib
import json
from decimal import Decimal
from pathlib import Path


def compile_settlement(input_dir: Path, cutoff_id: str, prior_state=None):
    """Return report, actions, reconciliation and serializable state."""
    trades = {}
    allocations = {}
    instructions = []
    for path in sorted(input_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            payload = row.get("payload", {})
            if row.get("kind") == "TRADE":
                trades[payload["trade_id"]] = (row, payload)
            elif row.get("kind") == "ALLOCATION":
                allocations[payload["allocation_id"]] = (row, payload)
            elif row.get("kind") == "INSTRUCTION":
                instructions.append((row, payload))

    report = []
    actions = []
    for row, ins in instructions:
        alloc = allocations.get(ins["allocation_id"], ({}, {}))[1]
        trade = trades.get(alloc.get("trade_id"), ({}, {}))[1]
        mismatch = any(str(ins.get(k)) != str(trade.get(k)) for k in ("side", "isin", "quantity", "cash_cents", "currency", "settlement_date", "place"))
        reason = "TRADE_MISMATCH" if mismatch else "COUNTERPARTY_PENDING"
        item = {
            "instruction_id": ins["instruction_id"],
            "trade_id": alloc.get("trade_id"),
            "allocation_id": ins["allocation_id"],
            "account": ins["account"],
            "status": "FAILED",
            "settled_quantity": "0",
            "settled_cash_cents": 0,
            "open_quantity": str(Decimal(str(ins["quantity"]))),
            "primary_reason": reason,
            "evidence_ids": sorted([row["event_id"]]),
        }
        report.append(item)
        actions.append({"instruction_id": ins["instruction_id"], "action": "WAIT", "open_quantity": item["open_quantity"], "preserve_final_quantity": "0", "evidence_ids": item["evidence_ids"]})
    report.sort(key=lambda x: x["instruction_id"])
    actions.sort(key=lambda x: x["instruction_id"])
    return {"report": report, "plan": [], "actions": actions, "reconciliation": [], "state": {"last_cutoff": cutoff_id, "records": []}}


def digest_bytes(parts):
    h = hashlib.sha256()
    for part in parts:
        h.update(part)
    return h.hexdigest()
