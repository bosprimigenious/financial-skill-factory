from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("13_现行服务.py")
SPEC = importlib.util.spec_from_file_location("risk_close_submission", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class PublicContractTests(unittest.TestCase):
    def test_empty_incremental_result_is_stable(self):
        state = MODULE.replay_incremental(None, [], "2026-09-30T18:00:00+08:00")
        result = state["result"]
        self.assertEqual(result["portfolios"], [])
        self.assertEqual(result["limit_checks"], [])
        self.assertEqual(result["release_groups"], [])
        self.assertEqual(len(result["digest"]), 64)

    def test_duplicate_delivery_is_idempotent(self):
        row = {
            "event_id": "RG1",
            "kind": "release_group",
            "stream_id": "release_group:G1",
            "revision": 1,
            "portfolio_ids": [],
            "release_group_id": "G1",
            "recorded_at": "2026-09-30T10:00:00+08:00",
        }
        one = MODULE.replay_incremental(None, [row], "2026-09-30T18:00:00+08:00")
        two = MODULE.replay_incremental(
            one,
            [json.loads(json.dumps(row))],
            "2026-09-30T18:00:00+08:00",
        )
        self.assertEqual(one["result"], two["result"])

    def test_digest_is_lower_hex(self):
        state = MODULE.replay_incremental(None, [], "2026-09-30T18:00:00+08:00")
        digest = state["result"]["digest"]
        self.assertRegex(digest, r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main(verbosity=2)

