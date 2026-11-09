"""Stage 2 · 业务决策链（DAG）与复杂度指标。

难度不来自附件数量，来自**一个前置判断改变会传播到下游多个结果**。
本模块只做两件事：把决策链画成图、把图数成 E/C/T/D/S/V/A。

注意：指标只用于内部选题排序，禁止写进题面或宣称达到平台二轮门槛。
"""
from __future__ import annotations

from dataclasses import dataclass, field

KINDS = ("evidence", "judgment", "action", "delivery")


@dataclass
class Node:
    id: str
    kind: str
    label: str
    time_dependent: bool = False                 # D2
    sensitive_to: tuple[str, ...] = ()           # D4 口径敏感性
    evidence_sources: tuple[str, ...] = ()       # D1：>=2 表示同一判断有多源证据
    constraints: tuple[str, ...] = ()            # D3 多约束

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"kind 必须是 {KINDS}，得到 {self.kind!r}")


@dataclass
class DecisionDAG:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)   # (from, to)

    def add(self, node: Node) -> "DecisionDAG":
        if node.id in self.nodes:
            raise ValueError(f"重复节点 {node.id}")
        self.nodes[node.id] = node
        return self

    def link(self, a: str, b: str) -> "DecisionDAG":
        for x in (a, b):
            if x not in self.nodes:
                raise KeyError(f"未知节点 {x}")
        self.edges.append((a, b))
        return self

    # ---------- 图算法 ----------
    def successors(self, nid: str) -> list[str]:
        return [b for a, b in self.edges if a == nid]

    def descendants(self, nid: str) -> set[str]:
        seen: set[str] = set()
        stack = list(self.successors(nid))
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            stack.extend(self.successors(x))
        return seen

    def predecessors(self, nid: str) -> list[str]:
        return [a for a, b in self.edges if b == nid]

    def cycles(self) -> list[list[str]]:
        bad: list[list[str]] = []

        def dfs(n: str, path: list[str]) -> None:
            for m in self.successors(n):
                if m in path:
                    bad.append(path[path.index(m):] + [m])
                else:
                    dfs(m, path + [m])

        for nid in self.nodes:
            dfs(nid, [nid])
        return bad

    # ---------- 指标 ----------
    def metrics(self) -> dict:
        nodes = list(self.nodes.values())
        E = len({s for n in nodes for s in n.evidence_sources})
        C = sum(1 for n in nodes if n.kind == "judgment" and len(n.evidence_sources) >= 2)
        T = sum(1 for n in nodes if n.time_dependent)
        D = sum(1 for n in nodes if n.kind == "judgment"
                and sum(1 for p in self.predecessors(n.id) if self.nodes[p].kind == "judgment") >= 2)
        S = len({s for n in nodes for s in n.sensitive_to})
        V = sum(1 for n in nodes if n.kind == "judgment" and n.evidence_sources)
        A = sum(1 for n in nodes if n.kind == "action")
        prop = {n.id: len(self.descendants(n.id)) for n in nodes if n.kind == "judgment"}
        return dict(E=E, C=C, T=T, D=D, S=S, V=V, A=A,
                    propagation_max=max(prop.values(), default=0),
                    propagation=prop)

    def complexity_flags(self, min_propagation: int = 2) -> list[str]:
        """返回'复杂度不足'的原因；空列表表示结构上够复杂。仅供内部参考。"""
        m = self.metrics()
        out = []
        if m["E"] < 3:
            out.append(f"独立证据源仅 {m['E']} 个（建议 >=3）")
        if m["C"] < 1:
            out.append("无实质证据冲突")
        if m["propagation_max"] < min_propagation:
            out.append(f"前置判断最多传播 {m['propagation_max']} 个下游结果（建议 >={min_propagation}）")
        if m["D"] < 1:
            out.append("无多前置依赖的决策节点")
        return out

    def validate(self) -> None:
        cyc = self.cycles()
        if cyc:
            raise ValueError(f"决策链存在环，无法确定计算顺序：{cyc[0]}")
        orphan = [n.id for n in self.nodes.values() if n.kind in ("evidence",) and not self.successors(n.id)]
        if orphan:
            raise ValueError(f"证据节点未连接到任何判断：{orphan}")
