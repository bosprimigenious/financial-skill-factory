"""Stage 1 · 金融任务识别与三级 Skill 匹配。

匹配不是关键词 → 词条，而是**动作动词 + 业务对象 + 交付物形态**三段打分：
    map_task("核验 6 家外包商 技术风险 定级 底稿") -> [Candidate(l2=信息科技外包风险管理, l3=..., score=0.8)]

唯一性由 registry 占用集负责：命中已占用的三级 Skill 直接标 blocked。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ACTION_HINTS = {
    "核验": ["核验", "核对", "复核", "勾稽", "对平"],
    "测算": ["测算", "计算", "估算", "折算", "重算"],
    "编制": ["编制", "定级", "出具", "形成", "提交"],
    "评估": ["评估", "评价", "评级", "判定"],
    "设计": ["设计", "拟定", "设定"],
}


@dataclass(frozen=True)
class Candidate:
    l2: str
    l3: str
    score: float
    platform: bool
    blocked: bool = False
    reason: str = ""


def _load_domains(yaml_path: str | Path) -> list[dict]:
    """极简 YAML 读取：只用本仓库 financial_domains.yaml 的子集语法。"""
    rows: list[dict] = []
    l2 = None
    cur = None
    for raw in Path(yaml_path).read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("- l2:"):
            l2 = s.split(":", 1)[1].strip()
            cur = None
        elif s.startswith("- l3:"):
            cur = {"l2": l2 or "?", "l3": s.split(":", 1)[1].strip(), "platform": False}
            rows.append(cur)
        elif cur is not None and s.startswith("platform:"):
            cur["platform"] = s.split(":", 1)[1].strip() == "true"
    return rows


def map_task(text: str, domains_yaml: str | Path, occupied: set[str] | None = None,
             top_k: int = 5) -> list[Candidate]:
    occupied = occupied or set()
    rows = _load_domains(domains_yaml)
    t = text or ""
    acts = [a for a, syn in ACTION_HINTS.items() if any(s in t for s in syn)]
    out: list[Candidate] = []
    for r in rows:
        l2, l3 = r["l2"], r["l3"]
        # 对象重合度：l2/l3 的 2-gram 命中率
        grams = {l3[i:i + 2] for i in range(len(l3) - 1)} | {l2[i:i + 2] for i in range(len(l2) - 1)}
        hit = sum(1 for g in grams if g in t)
        obj = hit / max(1, len(grams))
        act = 1.0 if any(a in l3 for a in acts) else 0.4
        score = round(0.75 * obj + 0.25 * act, 4)
        if score < 0.05:
            continue
        out.append(Candidate(l2, l3, score, bool(r["platform"]),
                             blocked=l3 in occupied,
                             reason="三级 Skill 已被占用" if l3 in occupied else ""))
    out.sort(key=lambda c: (-c.score, c.blocked))
    return out[:top_k]


def require_unique(cands: list[Candidate]) -> Candidate:
    """取分最高且未被占用的候选；全部被占用则报错。"""
    ok = [c for c in cands if not c.blocked]
    if not ok:
        raise LookupError("候选三级 Skill 均已被占用：" + ", ".join(c.l3 for c in cands[:3]))
    return ok[0]
