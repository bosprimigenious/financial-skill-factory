"""Risk replay entry points for 龙鳞."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


def evaluate_bundle(bundle_dir: str | Path, cutoff: str) -> dict[str, Any]:
    """Evaluate supported records in bundle_dir at cutoff."""
    raise NotImplementedError


def replay_incremental(
    state: dict[str, Any] | None,
    records: Iterable[dict[str, Any]],
    cutoff: str,
) -> dict[str, Any]:
    """Ingest records idempotently and return serializable state plus result."""
    raise NotImplementedError

