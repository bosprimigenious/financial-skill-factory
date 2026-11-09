# Financial Skill Factory · V1 计划

> 范围：**只做金融**。8 道题的题池、平台规则、提交口径见 `../expert-task-batch-20261109/`。
> 底座选型与源码证据见 [RESEARCH-SOURCE-LEVEL.md](RESEARCH-SOURCE-LEVEL.md)。
> 一句话：以 FinancialAuditBench（MIT）为引擎，把「真实案例 → 六类材料 → 独立复核 → 盲测 → 返修」做成可重复的产线；**不**做 AI 凭空批量出题。

## 1. 产线边界（先写死，避免跑偏）

| 允许自动化 | 必须人工/真实依据 |
|---|---|
| 材料盘点、结构化、哈希与版本 | 案例来源（真实工作经历、脱敏材料） |
| 题面/步骤/GT 的**草稿**与一致性检查 | 业务规则、口径、专业结论的确认 |
| Excel/CSV/Word 底稿生成与复算 | 岗位资质与能力标签的勾选 |
| Rubric 候选与重复考点检查 | 最终 rubric 的采纳与 Gate 判定 |
| 独立 Verifier、失败归因、返修改动单 | 「这道题值不值得交」的判断 |
| 六类材料打包与自检 | 平台提交动作 |

红线：合成材料（如 FinancialAuditBench 的 synthetic binder）只能做**工程夹具**，不得作为案例材料提交；不得改写公开 benchmark 任务后提交。

## 2. 目录

```text
financial-skill-factory/
  README.md                    入口与状态
  FINANCIAL_FACTORY_PLAN.md    本文件
  RESEARCH-SOURCE-LEVEL.md     底座调研与跑通证据
  factory/
    fsf.py                     CLI：ingest / check（M0）
    (M1) scan.py               金融材料体检：表结构、合计、跨文件引用
    (M2) pack.py               六类材料骨架 + 平台字段映射
    (M3) verify.py             独立复算（走 vendor 的 rubric/recalculate）
    (M4) runlog.py             豆包运行记录、步数与链接归档
  cases/<case-id>/             真实案例（case.yaml + materials/）
  packs/<task-id>/             产出的六类材料包（对齐 expert-task-batch 契约）
  out/                         盘点/报告/中间产物
  vendor/                      克隆的上游仓库（gitignore，不入库）
  .uv-cache/                   uv 缓存（gitignore）
```

## 3. 复用矩阵（上游模块 → 我们的能力）

| 我们的能力 | 复用来源 | 复用方式 | 需重写 |
|---|---|---|---|
| 多文件材料生成 | `synthetic_binders/priors/graph` + `projection` | 先做**工程夹具**；域包照它的「图→投影」结构写 | 金融域包（基金/投行/交易/合规），非审计 |
| 材料一致性 | `projection/workbook_finalize.py`、`cross_document.py` | 直接借「同一图投影多文件」思路 | 我们的域内不变量 |
| 确定性评分 | `grading/rubric.py` + `deterministic.py` + `comparison.py` | 用它的 rubric.json schema（selector + comparator + tolerance） | 平台 5–12 条口径的映射层 |
| 工作簿重算 | `grading/recalculate.py` | 直接用（LibreOffice 隔离重算） | 无 |
| 模板防篡改 | `grading/template_contract.py` | 直接用 | 无 |
| 证据预算 | `grading/evidence_contract.py` | 直接用（≤3 单元格/判据） | 无 |
| Agent 执行/评测 | `benchmark/agent.py` + Harbor | 后置；我们先用豆包网页/云电脑 | 运行记录适配 |
| 任务/Rubric 组织 | BankerToolBench、FAB | 借鉴结构与 judge 归因 | 不引入代码 |
| 材料预处理/Judge 报告 | Finch | 只参考流程 | 自建（无许可） |

## 4. 六类材料的生成路径

```text
case.yaml + materials/            ← 专家提供，真实、脱敏
        │  fsf ingest
        ▼
material-inventory.json/md        ← 文件、哈希、sheet 结构、重复检测
        │  fsf scan（M1）
        ▼
材料体检报告（缺项/口径冲突/可复算性）
        │  fsf pack（M2）
        ▼
Prompt / Ideal Steps / GT / Rubric 骨架（带 TODO 与证据锚点）
        │  人工补专业判断
        ▼
GT 底稿（Excel/CSV/Word）  ← 用 vendor 的 workbook 能力生成 + LibreOffice 重算
        │  fsf verify（M3）
        ▼
独立 Verifier 报告（公式/合计/单位/跨文件一致/答案泄露扫描）
        │  豆包工作任务模式 2.1Pro 实跑
        ▼
runlog + 评级评价（step 数、链接、附件）
        │  失败归因
        ▼
返修改动单 → 重新冻结 → 六类材料包
```

## 5. 里程碑

| 里程碑 | 交付 | 验收 |
|---|---|---|
| **M0 底座跑通** | vendor 安装、`fab` 可用、生成 64 文件夹具、`fsf ingest` 可用 | 已完成（见调研 §3） |
| M1 材料体检 | `factory/scan.py`：xlsx 合计/空值/重复/跨文件引用；输出体检报告 | 在 1 个真实案例上跑出「缺什么/哪里口径冲突」 |
| M2 六类材料骨架 | `factory/pack.py`：case + skill → pack 骨架（复用批次模板）；平台字段映射 | 产出的 pack 能被 `expert-task-batch` 的 `verify_batch.sh` 识别为 DRAFT |
| M3 独立复算 | `factory/verify.py`：借 vendor 的 rubric schema + recalculate；跑通 GT 复算 | GT 与 3 个负向样本的判定符合预期 |
| M4 盲测与返修 | `factory/runlog.py` + 返修改动单模板 | 一次实跑产出 step 数/链接/附件与归因 |

时间建议：M1 半周、M2 半周、M3 一周、M4 一周。先做 **01 持仓核对**与 **02 管理费**两题打通，再复制到其余 6 题。

## 6. 关键设计决定

1. **不 fork 上游当产品**：vendor 只读，我们的代码在 `factory/`；升级上游不改我们的逻辑。
2. **rubric 双轨**：平台提交用 5–12 条专家 rubric；内部用 vendor 的 selector 式 rubric 做机器复算。两者用 `RUBRIC-MAP.md` 对齐（平台条目 ↔ 机器检查）。
3. **案例即目录**：一个真实案例 = `case.yaml`（元数据 + required_files）+ `materials/`；所有产物可追溯到哈希。
4. **先夹具后真料**：工程能力用合成夹具验证（允许），交付必须真实材料（禁止伪装）。
5. **步数从设计来**：多文件证据链、逐条裁决、三对账、情景重算、自检回改；不靠拖时间（已由 119 条复核记录证实时长不再是门槛）。

## 7. 风险

| 风险 | 影响 | 处置 |
|---|---|---|
| 上游只覆盖审计域 | 基金/投行题不能直接生成材料 | 先做域包，不追求「万能生成器」 |
| LibreOffice/Docker 依赖 | M3 复算可能跑不起来 | 先验证 `soffice`，失败则用 openpyxl 公式解析兜底 |
| HF 任务包需授权/体积 | 无法复现上游评测 | 不依赖；我们只用其代码能力 |
| 合成材料红线 | 误把夹具当案例 | `case.yaml` 强制 `source_type: real|public|synthetic`，synthetic 禁止进 `packs/` |
| 许可证 | 商业使用风险 | 只用 MIT/Apache-2.0；NC/无许可不碰代码 |

## 8. 下一步（现在就能做）

1. 你给我**第一个真实案例**（01 持仓核对或 02 管理费），我跑 `fsf ingest` 出体检报告。
2. 同时我补 M1 `scan.py`（xlsx 合计/跨表引用），用生成夹具先自测。
3. 材料体检通过后，按六类材料出第一版包，再进 M3 复算。
