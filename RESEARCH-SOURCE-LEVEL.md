# 源码级调研：金融任务生产系统（2026-11-09）

> 目的：为一个**纯金融**的批量任务生产线选底座。判断标准只有四条：**能跑、许可可用、有确定性验证、能产出多文件金融材料**。
> 本文所有仓库信息来自 GitHub API / README / 源码目录（非二手转述）；「已跑通」的部分标注了本机命令与结果。

## 0. 结论先说

**选 `modus-audit/financial-audit-bench`（FinancialAuditBench，MIT）作为一底座。**
它是这批候选里唯一同时满足「今天就能在本机跑起来 + 有确定性 rubric/重算引擎 + 有多文件一致的材料生成器 + 许可允许改」的项目。其余项目按其强项做**模块级借鉴**，不整体引入：

| 项目 | 定位 | 用不用 |
|---|---|---|
| FinancialAuditBench | 底座：材料生成 + 确定性评分 + 复核 | **用（MIT，已跑通）** |
| BankerToolBench | 投行端到端任务 + Gandalf 代理式 verifier + Harbor | 借鉴 rubric/verifier 形态；不引入（依赖 Harbor + 15–20GB 工具数据） |
| FAB | 尽调任务 + 231 条 criteria + harness/judge | 借鉴任务/criteria 组织与 judge 归因；不引入（单公司虚构 data room） |
| Finch | JSONL→文件整理→预处理→Judge→Excel 报告 | 借鉴「材料预处理 + Judge 报告」；**无许可证，不复用代码** |
| Microsoft FinanceBenchmark | ERP/AP-AR 任务 + MCP + 自动评分 | 借鉴 MCP 取数与批量运行；不引入（依赖内部 ERP） |
| FinanceGym（google-research/finance_harness） | 研究型 agent + 任务构造方法 | 只读方法；**CC BY-NC，不用于生产** |
| FinProBench（论文） | RGRC：从专业交付物反推岗位 rubric | **无可运行仓库**，只采方法（岗位能力库） |

## 1. 候选事实表（已核实）

| 项目 | 仓库 | 许可 | 规模 | 入口 | 本机可跑 |
|---|---|---|---|---|---|
| FinancialAuditBench | `modus-audit/financial-audit-bench` | MIT（代码） | 240 文件 / 493 KB 源码；216 个 py | `uv run fab {generate-synthetic-binder,run,regrade}` | **是**（已 sync + 生成） |
| BankerToolBench | `Handshake-AI-Research/bankertoolbench` | Apache-2.0 | 45 文件 / 208 KB | `harbor run -c job.yaml` + `adapters/btb` | 需 Harbor + Docker + HF + 5.5 GB 工具数据 |
| FAB | `SecondState-ai/finance-agents-benchmark` | MIT（代码）/ 数据单独 | 3,909 文件 / 45 MB | `./scripts/run-task --task 001` + `./scripts/grade` | 需 uv + Docker + API key |
| Finch | `FinWorkBench/Finch` | **未见许可证声明** | 28 文件 / 358 KB | `src/prompt_build_pipeline.py`、`src/call_gpt_judge.py` | 需 Azure OpenAI |
| MS FinanceBenchmark | `microsoft/FinanceBenchmark` | MIT | 45 文件 / 32 MB | `uv run run_benchmark.py --provider claude` | 需 ERP MCP token |
| FinanceGym | `google-research/google-research` → `finance_harness/` | 仓库 Apache-2.0；**FinanceGym 数据 CC BY-NC** | 仓库 1.2 GB（子目录） | `python main.py -p "..."` | 可跑（agent），但数据许可限制商业用途 |
| FinProBench | 论文 arXiv 2608.04077 | — | — | — | **无官方仓库** |

补充核实：
- `Handshake-AI-Research/gandalf-the-grader` 存在，Apache-2.0（BTB 的 agentic verifier）。
- GitHub 搜索无 `FinProBench` 实现仓库；`FinanceGym` 也无可独立运行仓库（在 google-research 子目录内）。

## 2. FinancialAuditBench 源码结构（决定我们能复用多少）

```text
src/financial_audit_bench/
  cli.py                     generate-synthetic-binder / run / regrade
  benchmark/
    build.py  tasks.py  dataset.py  agent.py
    grading/                 ← 真正值钱的部分
      rubric.py              不可变 rubric 定义、校验、编译（793 行）
      deterministic.py       标量/覆盖/表记录检查（485 行）
      comparison.py          数值/日期/文本等价与容差
      lookup.py              答案定位、合并表头、缺失列
      recalculate.py         LibreOffice 无头重算（隔离副本，180s 超时）
      template_contract.py   用未改动的模板校验 rubric 选择器
      evidence_contract.py   证据预算（≤3 单元格/条）
      workbook.py  grade.py  judge.py  feedback.py  local.py
  synthetic_binders/         ← 材料生成引擎
    fsm.py  models.py  data_catalog.py
    priors/graph/            规则图（250 节点 / 1000 边量级）
      domains/{ap,ar,cash,inventory,fixed_assets,journal,payroll,receivables,tb}/…
      engine/                rule registry
    priors/graph_construction/  图 → 文档投影
      projection/documents/     发票、银行对账单、确认函、工资表、盘点表…
      projection/foundational_* 试算平衡、往来、收入、库存截止…
      projection/workbook_finalize.py
    _1_start … _6_validate_pbcs   六阶段流水线
docs/benchmark-tasks.md     任务/评分/结果目录约定
```

关键设计（可直接借）：

1. **先建图、再投影文档**：所有文件来自同一份数据图，天然保证余额/日期/交易互相一致；这正是「多文件金融材料」最难的部分。
2. **rubric 是数据不是代码**：`rubric.json` 用选择器（sheet/列/行键）+ 比较器 + 容差；`deterministic.py` 执行；`template_contract.py` 防止改模板骗分。
3. **重算隔离**：`recalculate.py` 复制工作簿到临时目录、强制 LibreOffice 重算，避免信任 OOXML 缓存——这就是我们要的「独立 Verifier」。
4. **证据预算**：一条判据最多选 3 个单元格，防止「写一堆文字蒙分」。

## 3. 本机跑通记录（M0 证据）

```bash
# uv 0.13.7（Homebrew 版 0.12.1 不满足 required-version，改用官方二进制，sha256 已核）
./vendor/uv/uv-aarch64-apple-darwin/uv --version   # uv 0.13.7

git clone --depth 1 https://github.com/modus-audit/financial-audit-bench.git
export UV_CACHE_DIR=$PWD/.uv-cache                  # 沙箱不能写 ~/.cache
../uv/uv-aarch64-apple-darwin/uv sync                # 成功（harbor/litellm/openai/openpyxl…）

uv run fab --help
# usage: fab [-h] {generate-synthetic-binder,run,regrade}

uv run fab generate-synthetic-binder manufacturing generated_binders/demo --seed 42
# Generated synthetic binder synthetic-261109083559 at generated_binders/demo
# real 0m4.075s
```

产物：**64 个文件 / 0.87 MB**（35 个 xlsx、28 个 txt、1 个 manifest），含 AR 账龄、存货截止、银行对账单、工资登记、试算平衡、确认函等，结构与 `pbc_package/`、`direct_to_auditor/`、`planning/` 分层。

复算：`uv run fab regrade` 需要任务包（HF 数据集）。**未下载**（体积与许可待核）；因此「评分链路」目前只有源码级把握，**没有本次运行证据**——这是本报告明确的不确定性。

## 4. 许可与红线

| 资源 | 许可 | 我们能做什么 |
|---|---|---|
| FinancialAuditBench 代码 | MIT | 可改、可商用、可闭源集成（保留版权声明） |
| FinancialAuditBench 数据（HF） | 需单独核验 | 只做内部测试；**不得**把其合成 binder 当作真实业务材料提交 |
| BankerToolBench 代码/数据 | Apache-2.0 / CC BY-4.0 | 可借鉴；不引入其评测集 |
| FAB 代码/数据 | MIT / 单独 | 同上 |
| Finch | 无许可 | **不复用代码**，只参考流程 |
| FinanceGym | CC BY-NC | **不用于生产**，只读方法 |
| FinProBench | 论文 | 只采 RGRC 方法 |

铁律（来自 11.4 与你的要求）：

1. 合成材料只能做**工程夹具/压力测试**，不能伪装成真实案例提交。
2. 不把任何公开 benchmark 的任务改数据后提交（红线：套用公开评测集）。
3. 真实案例、专家资质、业务判断不可自动化绕过。

## 5. 还差什么（诚实清单）

- 未跑 `fab run`（需要 HF 任务包 + 模型 key + Docker/Harbor 环境），所以「端到端评测」尚未验证。
- 未验证 LibreOffice 是否在 PATH（评分依赖 `soffice`）。
- 未验证 HF 数据集是否需要授权/体积。
- FinancialAuditBench 只覆盖审计域；基金/投行/交易/合规域的「域包」要自己写。
