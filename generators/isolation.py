"""Stage 3 · 生成隔离。

这是 V2 最重要的一段代码。它把"不能自己给自己判分"落成运行期断言：

    assert_disjoint(gt_inputs, rubric_inputs)   # 输入集合不相交
    seal(...)                                   # 生成时对输入做哈希并签发回执
    verify_seal(...)                            # 事后任何人可核对

没有回执的 GT 或 Rubric 不得进入题包（`quality_gates` 会查）。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

# 允许出现在输入声明里的类别；'gt' 与 'rubric' 互为禁区
ALLOWED = {
    "materials", "prompt", "rules", "verifiers", "registry", "dag", "profile",
    "gt", "rubric",
}
MUTUALLY_EXCLUSIVE = ({"gt", "rubric"},)


class IsolationError(RuntimeError):
    """出现了自我认证：一方看见了另一方的产物。"""


def assert_disjoint(gt_inputs: tuple[str, ...], rubric_inputs: tuple[str, ...]) -> None:
    """GT 与 Rubric 可以共享 materials/prompt/rules，但**不得读取对方产物**。

    共享输入是正常的（两边都要看题面和材料）；真正的自我认证是
    "Rubric 照着 GT 写" 或 "GT 照着 Rubric 凑"，这两种都必须拒绝。
    """
    if "rubric" in gt_inputs:
        raise IsolationError("GT 生成声明中包含 rubric 输入：GT 不得读取评分标准")
    if "gt" in rubric_inputs:
        raise IsolationError("Rubric 生成声明中包含 gt 输入：Rubric 不得读取标准答案")
    for name, says in (("gt", gt_inputs), ("rubric", rubric_inputs)):
        unknown = set(says) - ALLOWED
        if unknown:
            raise IsolationError(f"未登记的输入类别：{sorted(unknown)}")


def hash_inputs(refs: dict[str, str | Path]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, ref in refs.items():
        p = Path(str(ref))
        if p.is_file():
            out[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        elif p.is_dir():
            h = hashlib.sha256()
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    h.update(str(f.relative_to(p)).encode())
                    h.update(f.read_bytes())
            out[name] = h.hexdigest()
        else:
            out[name] = "sha256:" + hashlib.sha256(str(ref).encode()).hexdigest()
    return out


def seal(artifact: str, declared_inputs: tuple[str, ...], refs: dict[str, str | Path],
         out_dir: str | Path) -> dict:
    """签发隔离回执：产物名 + 声明输入 + 输入哈希 + 时间。"""
    if artifact.startswith("gt") and "rubric" in declared_inputs:
        raise IsolationError("GT 生成声明中包含 rubric 输入")
    if artifact.startswith("rubric") and "gt" in declared_inputs:
        raise IsolationError("Rubric 生成声明中包含 gt 输入")
    rec = {
        "artifact": artifact,
        "declared_inputs": list(declared_inputs),
        "input_hashes": hash_inputs(refs),
        "sealed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    d = Path(out_dir) / "seals"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{artifact}.seal.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
    return rec


def verify_seal(seal_path: str | Path, refs: dict[str, str | Path]) -> bool:
    """输入变了则回执失效（材料被换 = 旧 GT 不再可信）。"""
    rec = json.loads(Path(seal_path).read_text(encoding="utf-8"))
    return rec.get("input_hashes") == hash_inputs(refs)
