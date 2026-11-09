"""Stage 3B · 作答思路生成。

从决策 DAG 的拓扑序推出执行路径：证据节点 → 判断节点 → 动作节点 → 交付节点。
每一步必须写清四件事：读什么、做什么、判什么、错了怎么办。
"""
from __future__ import annotations

from task_architect.complexity import DecisionDAG, Node


def topo(dag: DecisionDAG) -> list[str]:
    dag.validate()
    indeg = {n: len(dag.predecessors(n)) for n in dag.nodes}
    ready = [n for n, d in indeg.items() if d == 0]
    order: list[str] = []
    while ready:
        ready.sort()
        n = ready.pop(0)
        order.append(n)
        for m in dag.successors(n):
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
    if len(order) != len(dag.nodes):
        raise ValueError("决策链存在无法排序的节点（环或孤立）")
    return order


def build(dag: DecisionDAG, *, exceptions: dict[str, str] | None = None) -> str:
    exc = exceptions or {}
    lines = ["# 作答思路（由决策链生成）", "",
             "| 步 | 节点 | 类型 | 读什么 | 判什么 | 异常处理 |", "|---:|---|---|---|---|---|"]
    for i, nid in enumerate(topo(dag), 1):
        n: Node = dag.nodes[nid]
        read = "、".join(n.evidence_sources) or ("材料清单" if n.kind == "evidence" else "上游节点结论")
        judge = n.label if n.kind in ("judgment", "action") else f"取得：{n.label}"
        lines.append(f"| {i} | {nid} | {n.kind} | {read} | {judge} | {exc.get(nid, '登记待核，不得自拟口径')} |")
    m = dag.metrics()
    lines += ["", f"复杂度：E={m['E']} C={m['C']} T={m['T']} D={m['D']} S={m['S']} V={m['V']} A={m['A']}；"
                  f"最大传播度={m['propagation_max']}",
              "", "> 复杂度指标仅用于内部排序，不写进题面，不作为难度门槛依据。"]
    return "\n".join(lines)
