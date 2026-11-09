# 架构

```text
cases/<case>/           真实案例（case.yaml + materials/）
        │  fsf ingest
        ▼
out/<case>/material-inventory.{json,md}     文件、哈希、sheet 结构、重复
        │  fsf scan / check
        ▼
out/<case>/scan-report.{json,md}            缺项 / 空表 / 重复 / 口径检查（xlsx_cell、行数）
        │  fsf pack
        ▼
packs/<task>/           六类材料骨架 + 平台字段 + 三类附件槽
        │  人工补 GT / rubric / ideal steps
        ▼
04_evidence/            豆包运行记录、judge 分、步数、C20
        │  （M3）verify
        ▼
独立复算报告 → 返修改动单 → 重新冻结
```

## 模块

| 模块 | 职责 | 状态 |
|---|---|---|
| `fsf.util` | 哈希、遍历、极小 YAML 解析、case 加载 | ✅ |
| `fsf.ingest` | 材料盘点（xlsx sheet 结构、csv 行数、重复哈希） | ✅ |
| `fsf.scan` | 体检与声明式检查（xlsx_cell / 行数 / 格式 / 大小） | ✅ |
| `fsf.pack` | 六类材料骨架、平台字段、附件槽；拒绝 synthetic | ✅ |
| `fsf.verify`（M3） | 借上游 rubric schema + LibreOffice 重算，GT 独立复算 | ⬜ |
| `fsf.runlog`（M4） | 豆包运行记录、链接、步数、评级 | ⬜ |
| `fsf.revise`（M4） | 失败归因 → 返修改动单 | ⬜ |

## 与上游的关系

- `vendor/financial-audit-bench` 是**只读引擎**（MIT），不入库。
- 我们不 fork 它；需要复算能力时，以子进程/库调用的方式使用其 `grading/recalculate.py` 与 `rubric.py` 的 schema。
- 上游的 `synthetic_binders` 只用于生成**工程夹具**，验证材料引擎与我们的体检器；不得进入 `packs/`。

## 硬约束

1. `pack` 拒绝 `source_type: synthetic`。
2. `packs/` 与 `cases/` 默认不进版本库（真实材料）。
3. 体检 FAIL 不允许进入打包；WARN 需人工判断。
4. 所有产物可追溯到输入哈希。
