# Financial Skill Factory

真实金融案例驱动的任务生产线：**案例 → 材料体检 → 六类材料 → 独立复核 → 盲测 → 返修**。
只做金融；不做 AI 凭空批量出题，不把合成材料包装成真实业务。

> 状态：**M0 完成**（底座跑通、CLI 可用、6 个单元测试通过）。真实案例尚未接入。

## 为什么是这条路线

- 底座选 [FinancialAuditBench](https://github.com/modus-audit/financial-audit-bench)（MIT）：自带「图 → 多文件投影」生成器与确定性 rubric/重算引擎，已在本机跑出 64 文件的多文件夹具。
- 其余金融 benchmark 只做模块级借鉴：BankerToolBench（Apache-2.0）、FAB（MIT）、Finch（无许可，不取代码）、FinanceGym（CC BY-NC，不取代码）、FinProBench（论文，无仓库）。
- 详见 [RESEARCH-SOURCE-LEVEL.md](RESEARCH-SOURCE-LEVEL.md) 与 [FINANCIAL_FACTORY_PLAN.md](FINANCIAL_FACTORY_PLAN.md)。

## 快速开始

```bash
# 0) 依赖：Python 3.10+，openpyxl；建议用上游 venv，避免另装
PY=vendor/financial-audit-bench/.venv/bin/python   # 或系统 python（需 pip install openpyxl）

# 1) 材料盘点
PYTHONPATH=src $PY -m fsf ingest cases/<case-id>/materials --out out/<case-id>

# 2) 材料体检（FAIL 时非零退出）
PYTHONPATH=src $PY -m fsf scan cases/<case-id> --out out/<case-id>
PYTHONPATH=src $PY -m fsf check cases/<case-id>

# 3) 生成六类材料骨架
PYTHONPATH=src $PY -m fsf pack cases/<case-id> --out packs --platform-id <id>

# 4) 测试
make test
```

## 产出结构

```text
packs/<task-id>/
  00_meta.json                     案例/技能/平台 ID/来源类型
  01_public/task_prompt.md         题面（材料 1）
  01_public/data/                  输入附件（材料 1 的附件槽）
  02_platform_fields/              expert_profile / expert_rubric / ideal_steps / rating / hidden_difficulties
  03_private_review/GT/            Golden Response（材料 3，只进理想回复槽）
  04_evidence/                     运行日志、judge、步数、C20
  05_submission/                   三类附件槽 + READINESS.md
```

## 案例契约

```text
cases/<case-id>/
  case.yaml       # id/title/source_type/industry/l2_skill/level3_skill/required_files/checks
  materials/      # 真实、脱敏的输入材料
```

- `source_type: real | public | synthetic`；**synthetic 会被 `pack` 直接拒绝**，只能留在 `out/` 做工程夹具。
- `checks` 支持 `xlsx_cell`（sheet/cell/期望值/容差）与 `csv_min_rows` / `xlsx_sheet_min_rows`。
- 完整字段见 [cases/README.md](cases/README.md)。

## 边界

1. **真实案例优先**；合成数据只做工程测试。
2. **不套用公开评测集**：上游仓库是引擎，不是题库。
3. **专业判断不可自动化**：业务规则、口径、结论必须有人背书。
4. **许可**：只用 MIT / Apache-2.0 的代码；CC BY-NC 与无许可项目不复用代码。

## 文档

| 文档 | 内容 |
|---|---|
| [docs/SUBMISSION-SPEC.md](docs/SUBMISSION-SPEC.md) | 交什么包、什么格式、要哪些字段（以平台为准） |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 模块边界与数据流 |
| [FINANCIAL_FACTORY_PLAN.md](FINANCIAL_FACTORY_PLAN.md) | M0–M4 路线、复用矩阵 |
| [RESEARCH-SOURCE-LEVEL.md](RESEARCH-SOURCE-LEVEL.md) | 7 个候选的源码级调研与跑通证据 |

## 已知缺口

- 本机无 LibreOffice，上游的确定性重算暂不可用（备选：安装 LibreOffice 或用 `formulas` 库）。
- 未下载 HF 任务包，`fab run/regrade` 未验证。
- M2 的 `pack` 只生成骨架，GT 内容与 rubric 判分点仍需人工/专家确认。
- M3 独立复算、M4 盲测与返修尚未实现。
