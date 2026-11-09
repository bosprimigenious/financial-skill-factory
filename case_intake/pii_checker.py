"""Stage 0 · PII 扫描。

只做**发现与阻断**，不做自动改写——脱敏是人工决定，脚本擅自替换会把证据链改坏。
高危（阻断）：身份证、银行卡、手机号、护照。
中危（警告）：邮箱、统一社会信用代码、车牌。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PATTERNS = [
    ("id_card", "high", re.compile(r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")),
    ("bank_card", "high", re.compile(r"(?<!\d)(?:62|4\d|5[1-5])\d{14,17}(?!\d)")),
    ("mobile", "high", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("passport", "high", re.compile(r"(?<![A-Za-z0-9])[EGDSP]\d{8}(?![A-Za-z0-9])")),
    ("email", "medium", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("uscc", "medium", re.compile(r"(?<![A-Z0-9])[0-9A-HJ-NPQRTUWXY]{18}(?![A-Z0-9])")),
    ("plate", "medium", re.compile(r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-HJ-NP-Z][A-HJ-NP-Z0-9]{4,5}[A-HJ-NP-Z0-9挂学警港澳]")),
]


@dataclass(frozen=True)
class Hit:
    kind: str
    severity: str
    where: str
    masked: str

    def __str__(self) -> str:
        return f"{self.severity}:{self.kind}@{self.where}:{self.masked}"


def _mask(s: str) -> str:
    if len(s) <= 4:
        return "*" * len(s)
    keep = max(2, len(s) // 6)
    return s[:keep] + "*" * (len(s) - keep * 2) + s[-keep:]


def scan_text(text: str, where: str = "text") -> list[Hit]:
    out: list[Hit] = []
    for kind, sev, rx in PATTERNS:
        for m in rx.finditer(text or ""):
            out.append(Hit(kind, sev, where, _mask(m.group(0))))
    return out


def scan_paths(paths: list[str | Path]) -> list[Hit]:
    hits: list[Hit] = []
    for p in paths:
        p = Path(p)
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hits.extend(scan_text(text, where=str(p)))
    return hits


def blocking(hits: list[Hit]) -> list[Hit]:
    return [h for h in hits if h.severity == "high"]
