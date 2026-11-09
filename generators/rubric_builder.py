"""Stage 3D · Rubric 生成（独立于 GT）。

输入只有：题面、材料字段清单、口径文本（可选）、权重表。
**不读 GT**，也不读 GT 的任何中间产物——隔离由 `generators.isolation` 强制。

抽考点规则（可判、正交、可溯源）：
  1. 题面每一条"交付要求/D 项"至少对应一条考点（覆盖性）
  2. 一条考点只查一件事
  3. 每条考点必须挂到材料里的具体字段（证据锚点）
  4. 每条自带 tolerance 与 accepted_alternatives
  5. 权重合计必须恰 100
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

LAYER_HINTS = [
    ("L1", ("结论", "等级", "名单", "是否", "判定", "达标", "入选", "处置")),
    ("L3", ("依据", "编号", "字段", "定位", "来源", "勾稽", "对平", "证据", "原文")),
    ("L2", ("计算", "公式", "折算", "取用", "排序", "计数", "计提", "测算")),
    ("L4", ("审批", "办理", "停止", "回滚", "责任", "时限", "签批", "执行")),
]
NUM_HINT = re.compile(r"(≥|≤|>|<|=|不超过|不低于)?\s*\d+(?:\.\d+)?")


@dataclass
class RubricItem:
    id: str
    layer: str
    statement: str
    weight: int
    tolerance: str = "整数精确值"
    accepted_alternatives: list[str] = field(default_factory=list)
    evidence_anchor: str = ""
    zero_example: str = ""      # 0 分反例：模型最可能的错法
    source: str = ""            # 来自题面哪一条


@dataclass
class Rubric:
    task_id: str
    items: list[RubricItem] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(i.weight for i in self.items)

    def to_dict(self) -> dict:
        return {"task_id": self.task_id, "total": self.total,
                "items": [asdict(i) for i in self.items]}


def _section(text: str, *heads: str) -> str:
    for h in heads:
        i = text.find(h)
        if i >= 0:
            j = len(text)
            for nxt in ("【", "\n\n\n"):
                k = text.find(nxt, i + len(h))
                if k > i:
                    j = min(j, k)
            return text[i:j]
    return ""


def parse_requirements(prompt: str) -> list[tuple[str, str]]:
    """从题面抽出 (编号, 要求原文)。优先取【交付要求】段，退回 D 项。"""
    sec = _section(prompt, "【交付要求", "交付要求（硬性）", "交付要求")
    out = []
    if sec:
        for m in re.finditer(r"^(\d+)\.\s*(.+?)(?=\n\d+\.\s|\Z)", sec, re.M | re.S):
            out.append((m.group(1), " ".join(m.group(2).split())))
    if not out:
        for m in re.finditer(r"^(D\d+)\s*(.+?)(?=\nD\d+\s|\Z)", prompt, re.M | re.S):
            out.append((m.group(1), " ".join(m.group(2).split())))
    return out


def _layer(text: str) -> str:
    """按关键词命中数判层；同分时按 L1>L2>L3>L4 取。

    一条交付要求常同时含多类线索，取"最强线索"比"第一个命中"稳定。
    """
    score: dict[str, int] = {}
    for name, keys in LAYER_HINTS:
        score[name] = sum(1 for k in keys if k in text)
    best = max(score.values())
    if best == 0:
        return "L2"
    for name in ("L1", "L2", "L3", "L4"):
        if score[name] == best:
            return name
    return "L2"


def _anchor(text: str, fields: dict[str, list[str]]) -> str:
    """在题面文字里找材料字段/文件名的 2-gram 命中，作为证据锚点。"""
    def grams(x: str) -> set[str]:
        return {x[i:i + 2] for i in range(len(x) - 1)}

    hits = []
    for f, cols in fields.items():
        for c in [*cols, f]:
            if not c:
                continue
            if grams(c) & grams(text):
                hits.append(f"{f}#{c}")
                break
    return "; ".join(hits[:2]) or "（需人工补锚点）"


def _tolerance(text: str) -> str:
    if NUM_HINT.search(text):
        return "数值按题面给出的容差；未给定时整数精确、金额 0.01、比例 1e-6"
    return "二值判定（是/否）"


def allocate_weights(n: int, explicit: list[int] | None = None) -> list[int]:
    if explicit:
        if len(explicit) != n:
            raise ValueError(f"权重个数 {len(explicit)} 与考点数 {n} 不符")
        if sum(explicit) != 100:
            raise ValueError(f"权重合计 {sum(explicit)} ≠ 100")
        return list(explicit)
    base, rem = divmod(100, n)
    return [base + (1 if i < rem else 0) for i in range(n)]


def build(*, task_id: str, prompt: str, materials_fields: dict[str, list[str]],
          weights: list[int] | None = None, zero_examples: dict[int, str] | None = None
          ) -> Rubric:
    reqs = parse_requirements(prompt)
    if not reqs:
        raise ValueError("题面里找不到交付要求（【交付要求】编号段或 D1..Dn），无法独立抽考点")
    ws = allocate_weights(len(reqs), weights)
    items: list[RubricItem] = []
    for i, ((no, txt), w) in enumerate(zip(reqs, ws), 1):
        items.append(RubricItem(
            id=f"R{i}", layer=_layer(txt), statement=txt, weight=w,
            tolerance=_tolerance(txt), evidence_anchor=_anchor(txt, materials_fields),
            zero_example=(zero_examples or {}).get(i, ""), source=f"题面第{no}条"))
    r = Rubric(task_id, items)
    if r.total != 100:
        raise ValueError(f"权重合计 {r.total} ≠ 100")
    return r


def to_markdown(r: Rubric) -> str:
    out = [f"# 冻结考点（12 项制 / 合计 {r.total} 分）", "",
           "| 编号 | 层级 | 分值 | 考点 | 证据锚点 | 容差 | 0 分反例 |", "|---|---|---:|---|---|---|---|"]
    for i in r.items:
        out.append(f"| {i.id} | {i.layer} | {i.weight} | {i.statement[:80]} | {i.evidence_anchor} | "
                   f"{i.tolerance} | {i.zero_example or '—'} |")
    out += ["", "> 本表由 `generators/rubric_builder.py` 从题面交付要求独立抽取，未读取标准答案。"]
    return "\n".join(out)
