# Financial Skill Factory

> **分支说明**：`main` 是 V1（已跑通 1 个成品题包 + 9 个实例）。
> `v2` 是正在演进的产线改造：[V2-AUDIT.md](V2-AUDIT.md)（先审计）→ [V2-PLAN.md](V2-PLAN.md)（八阶段方案）→
> `make v2-test` / `make v2-smoke`。V1 的产物与实例不受影响。

真实金融工作任务的**出题产线**：案例 → 材料契约 → 冻结考点 → 标准答案 → 逐条判分 → 提交前 12 项检查。
只做金融；不凭空批量出题；不把合成材料包装成真实业务。

| 项 | 值 |
|---|---|
| 产线版本 | **V2（当前开发线）**；V1.1 保留为历史基线（见 [V2-PLAN.md](V2-PLAN.md)） |
| 成品题包 | 1 个：`packs/7689005313907642138/`（城商行 IT 外包供应商技术风险定级） |
| 实例库 | **9 个**：`cases/<题目 ID>/`（平台原件 + 来源与 sha256），见 [cases/INSTANCES.md](cases/INSTANCES.md) |
| 机器校验 | `tools/verify_pack.py` **47/47 PASS** |
| 单元测试 | `make test` 6/6 OK |
| 平台状态 | 未提交（见文末「诚实边界」） |


## V2：两套金融产线能力已整合

当前 `integration/expert-task-pipeline-v2` 是将另一仓库的通用批次工具移植到本仓库 V2 的集成分支。两个 GitHub 仓库原本没有共同分支祖先，因此不是跨仓库原生 merge commit；集成时保留本仓库 V2 的金融验证器、隔离生成器、真实性门禁和质量门禁，移植精确的八题 Task ID/L2/L3 登记、专业域目录、批次建题与 fail-closed 打包工具。

- 八题官方任务登记：`finance/batch/selected_tasks.json`
- 平台 Skill 映射：`finance/skill_registry.json` + `finance/domain_catalog.json`
- 建题：`tools/new_task.py`
- 批次打包：`tools/package_batch.py`
- 集成说明：[docs/BRANCH-INTEGRATION.md](docs/BRANCH-INTEGRATION.md)

### 八题脚手架操作

```bash
# 建立八个独立案例骨架，并生成 8 个小包 + 1 个总包（SCAFFOLD）
make batch-scaffold

# 执行批次单元测试
make batch-test

# 只有所有正式门禁完成后才可尝试 AUTHOR 包；未就绪会 fail closed
make batch-release
```

默认案例工作目录为 `work/financial-eight/cases/`，输出目录为 `dist/financial-eight/`。这两个目录不覆盖原有 `cases/<平台ID>/` 实例库。

## 这条产线解决什么

出题最难的不是"写一道难题"，是**证明它难且可判**。所以这里把两件事做成机器可校验的：

1. **可判**：考点是二值判定（整组闭合／不闭合），每条带数值容差与"0 分反例"，不存在"考虑了 XX"这种灰度表述。
2. **可复算**：材料由脚本生成，脚本内断言逐格对齐冻结考点。改一行数据，断言立刻告诉你哪一格崩了。

## 六道闸门

| 闸 | 名字 | 通过判据 | 失败即 |
|---|---|---|---|
| G1 | 选题 | 金融行业 + 材料可逐条复算 + 有实测证据 | 退回选题 |
| G2 | 材料契约 | 每件附件的行数、必备字段、必须埋的陷阱都写死 | 材料重做 |
| G3 | 冻结考点 | 12 条、权重合计恰 100、每条可判 TRUE/FALSE | 不许开工 |
| G4 | 标准答案 | 文字答案 + 答案附件，逐条对应考点 | 不许自测 |
| G5 | 当前 FDE 11.4 难度门槛 | 平台 Judge ≤50 **且** 官方单轮模型调用步数 ≥50；时长仅用于评级 | 修题重测 |
| G6 | 提交前 12 项 | 12/12 PASS | 不许领题 |

细节与反例写法见 [PIPELINE.md](PIPELINE.md)。

## 快速开始

```bash
# 0) 依赖：Python 3.10+ / openpyxl（建议用上游 venv，避免另装）
PY=vendor/financial-audit-bench/.venv/bin/python

# 1) 重新生成实例的材料 + 标准答案附件（脚本内断言逐格对齐考点）
$PY cases/ccb-vendor-tpr-2026/build_case.py --pack packs/7689005313907642138

# 2) 机器校验题包（材料行数、权重、隔离、勾稽、GT 五表、门槛）
$PY tools/verify_pack.py packs/7689005313907642138

# 3) 单元测试
make test
```

第 1 步会打印 48 格判定矩阵与断言结果；第 2 步 47 项全 PASS 才可提交。
**确定性**：同一输入重跑产出逐字节一致（含 GT xlsx 内部 zip 时间戳已归一），可直接 diff。

## 目录

```text
cases/7689005313907642138/materials/      平台原件（12 件 CSV，21,736 字节）
cases/<其余 8 个 ID>/materials/           平台原件（zip 解包 / PDF / md+csv）
cases/INSTANCES.md + cases/registry.json  实例库索引（9 个，含实测分与 sha256）
cases/ccb-vendor-tpr-2026/build_case.py   单一事实源：材料 12 件 CSV + GT 5 表 + 断言
packs/7689005313907642138/
  00_meta.json                  选题元数据、权重、实测、门槛核算
  01_public/task_prompt.md      题面（被试包唯一入口，含合成数据说明）
  01_public/data/*.csv          被试材料 12 件（307 行）
  02_platform_fields/           考点 12 条 / 隐藏难点 14 / 作答思路 50 步 / 材料契约 / 修订记录
  03_private_review/GT/         标准答案：文字 + xlsx 五表（D1/D4/D8/D9/D10）
  04_evidence/                  逐条判分、自测与门槛核算
  05_submission/                12 项检查、就绪说明
packs/SELECTION-FROM-119.md     从 119 条二轮质检记录里选这一题的漏斗与对照
tools/verify_pack.py            题包机器校验（47 项）
```

**隔离**：被试包只有 `01_public/`。考点、难点、答案、判分记录一律不进被试包；打包后核对 ZIP 清单，不能只看目录。

## 实例：城商行 IT 外包供应商技术风险定级

- 6 家供应商 × 8 个维度 = **48 格**；综合级 高 5 / 中 0 / 低 1。
- 12 条考点 = 100 分，其中 6 条在实测卷整组失守（54 分），得分 **46/100**。
- 隐藏难点 14 项，其中最硬的三处：附件12 规定"按核查范围合计取"（取单范围最大会把 V6 从高降到中）、附件7 的**组件供应商角色**（用附件1 列归并会把 SP-W 从 5 户缩成 1 户）、5 处恰等边界（`≥2`／`≥5`／`≥3`／`≤1 倍`／当日到期）。
- 门槛：46 ≤ 50，且 2916 秒 > 2400 秒 → **按现行书面口径达标**。

选题过程见 [packs/SELECTION-FROM-119.md](packs/SELECTION-FROM-119.md)：从 119 条记录经 5 步漏斗收敛到 1 条。

## 诚实边界

- **材料是合成数据**：机构匿名、供应商编号化，题面已明示。不是真实机构资料。
- **豆包未重跑**：46/100 与 48.6 分钟引自平台记录，属记录采信，不是本仓库实测。
- **平台未提交**：仓库状态是 `LOCAL_ACCEPTED`（门槛侧），不等于平台通过。
- **一处考点修订**：R1 分部计数原写「中7/低29」与 R2–R8 矛盾，已改为「中9/低27」并留痕，见 `02_platform_fields/RUBRIC-AMENDMENTS.md`。

## 参考文献与取舍

底座思路借自 [FinancialAuditBench](https://github.com/modus-audit/financial-audit-bench)（MIT，确定性 rubric 与重算引擎），其余金融 benchmark 只做模块级借鉴，详见 [RESEARCH-SOURCE-LEVEL.md](RESEARCH-SOURCE-LEVEL.md) 与 [FINANCIAL_FACTORY_PLAN.md](FINANCIAL_FACTORY_PLAN.md)。

## License

MIT，见 [LICENSE](LICENSE)。
