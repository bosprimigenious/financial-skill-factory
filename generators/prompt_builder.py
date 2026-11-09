"""Stage 3A · 题面生成。

只写四样东西：输入、目标、边界、交付物。**不写结论、不写阈值、不写考点。**
写完自检一次"泄露扫描"：出现结论性表述或考点用语即拒绝输出。
"""
from __future__ import annotations

import re

BANNED = ("标准答案", "考点", "判据", "得分", "满分", "答案是", "正确答案", "应当判为", "建议结论")

TEMPLATE = """{role}

【可用材料】
{materials}

【判定口径】
口径只写在材料中的制度/标准文件内，题面不复述、不提示阈值、不指出边界值。

【任务：交付物】
{deliverables}

【交付要求（硬性）】
{requirements}

【边界】
仅可依据材料作答；材料未提供的信息须登记为待核，不得自行补齐；不得使用外部检索结果替代材料。
"""


def leak_scan(text: str) -> list[str]:
    return [w for w in BANNED if w in text]


def build(*, role: str, materials: list[str], deliverables: list[str],
          requirements: list[str]) -> str:
    if len(deliverables) < 2:
        raise ValueError("交付物少于 2 项：单产物任务难以形成逐条判分的复核链")
    if len(requirements) < 6:
        raise ValueError(f"硬性交付要求仅 {len(requirements)} 条，不足以构成可复核义务")
    text = TEMPLATE.format(
        role=role.strip(),
        materials="\n".join(f"{i}) {m}" for i, m in enumerate(materials, 1)),
        deliverables="\n".join(deliverables),
        requirements="\n".join(f"{i}. {r}" for i, r in enumerate(requirements, 1)))
    bad = leak_scan(text)
    if bad:
        raise ValueError(f"题面出现泄露性表述：{bad}")
    if re.search(r"\d+\s*分", text):
        raise ValueError("题面出现分数字样，疑似泄露评分标准")
    return text
