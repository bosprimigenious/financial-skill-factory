"""Stage 0 · 案例来源登记。

V1 的教训：材料被换掉而没人知道（`packs/.../MATERIAL-DIVERGENCE.md`）。
所以登记的核心不是"记录一下来源"，而是**材料哈希绑定**：登记后材料被改，`verify_hashes`
必须报错，题包不得继续用。

用法：
    src = CaseSource.load("cases/7689005313907642138")
    CaseSource.verify_hashes("cases/7689005313907642138", src)   # 不符则抛 MaterialChanged
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

VALID_SOURCE_TYPES = ("real", "public", "synthetic")


class MaterialChanged(RuntimeError):
    """登记后材料发生变化。"""


@dataclass(frozen=True)
class CaseSource:
    case_id: str
    title: str
    provenance: str                      # 坐标：Base/table、URL、合同编号；必须可定位
    source_type: str                     # real | public | synthetic
    collected_at: str                    # ISO8601
    as_of: str | None = None             # 业务截止时点
    released_at: str | None = None       # 公开资料的发布日（public 必填）
    authorized: bool = False             # real 必填 True
    desensitized: bool = False           # real 必填 True
    owner: str = ""
    level3_skill: str = ""
    synthetic_disclosed_in_prompt: bool = False
    materials: dict[str, str] = field(default_factory=dict)   # rel_path -> sha256

    # ---------- 构造 ----------
    @staticmethod
    def scan_materials(case_dir: str | Path) -> dict[str, str]:
        root = Path(case_dir) / "materials"
        out: dict[str, str] = {}
        if not root.is_dir():
            return out
        for p in sorted(root.rglob("*")):
            if p.is_file():
                h = hashlib.sha256(p.read_bytes()).hexdigest()
                out[str(p.relative_to(root))] = h
        return out

    @classmethod
    def register(cls, case_dir: str | Path, **kw) -> "CaseSource":
        case_dir = Path(case_dir)
        if kw.get("source_type") not in VALID_SOURCE_TYPES:
            raise ValueError(f"source_type 必须是 {VALID_SOURCE_TYPES}，得到 {kw.get('source_type')!r}")
        src = cls(case_id=kw.pop("case_id", case_dir.name), materials=cls.scan_materials(case_dir), **kw)
        (case_dir / "source_registry.json").write_text(
            json.dumps(asdict(src), ensure_ascii=False, indent=2), encoding="utf-8")
        return src

    @classmethod
    def load(cls, case_dir: str | Path) -> "CaseSource":
        p = Path(case_dir) / "source_registry.json"
        if not p.is_file():
            raise FileNotFoundError(f"{p} 不存在：案例未登记，禁止进入生成环节")
        d = json.loads(p.read_text(encoding="utf-8"))
        return cls(**d)

    # ---------- 校验 ----------
    def manifest_rows(self) -> list[dict]:
        return [{"file": k, "sha256": v} for k, v in sorted(self.materials.items())]

    @staticmethod
    def verify_hashes(case_dir: str | Path, src: CaseSource) -> None:
        actual = CaseSource.scan_materials(case_dir)
        added = sorted(set(actual) - set(src.materials))
        removed = sorted(set(src.materials) - set(actual))
        changed = sorted(k for k in set(actual) & set(src.materials) if actual[k] != src.materials[k])
        if added or removed or changed:
            raise MaterialChanged(
                f"材料与登记不符：新增={added} 缺失={removed} 变更={changed}；"
                "处理方式：确认材料变更合理后重新 register，不得静默继续")
