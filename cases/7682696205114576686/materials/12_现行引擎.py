from __future__ import annotations


def run(input_dir, cut_id, prior_state=None):
    """Restore the fee ledger from the supplied event files."""
    return {
        "order_control": [],
        "allocation_fees": [],
        "correction_journal": [],
        "state": {"schema_version": 1, "cut_id": cut_id, "raw_facts": []},
    }
