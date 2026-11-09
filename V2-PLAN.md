# Financial Skill Factory V2 方案

基线审计见 [V2-AUDIT.md](V2-AUDIT.md)。V1 保留在 `main`；V2 在 `v2` 分支并行演进，不动已交付的题包。

## 一句话差别

V1：`材料 → 模板渲染 → 自证校验`
V2：`真实案例 → 门禁 → 技能匹配 → 决策链 → 四段独立生成 → 独立计算验证 → 盲测记录 → 提交门禁`

**核心约束**：出题、写 GT、写 Rubric、证明合格，四件事不能由同一份输入或同一个进程完成。
V2 用 `generators/isolation.py` 把这条约束写成可执行断言，而不是写在文档里。

## 八阶段与落地状态

| Stage | 模块 | 状态 | 关键产物 |
|---|---|---|---|
| 0 Case Registry | `case_intake/source_registry.py` | ✅ | `CaseSource` + 授权/脱敏/性质/时间线；sha256 清单 |
| 0 真实性门禁 | `case_intake/authenticity_gate.py` | ✅ | 7 条门禁 → `GateResult`（拒绝即不进入生成） |
| 0 PII 扫描 | `case_intake/pii_checker.py` | ✅ | 身份证/手机/卡号/邮箱/统一社会信用代码 → 报告 |
| 1 Skill Mapper | `task_architect/skill_mapper.py` | ✅ | 文本 → (L2, L3) 候选 + 三级唯一性检查 |
| 2 Task Architect | `task_architect/complexity.py` | ✅ | 决策 DAG + E/C/T/D/S/V/A + 传播度 |
| 3A Prompt | `generators/prompt_builder.py` | ✅ | 只写输入/目标/边界/交付，不写结论 |
| 3B Ideal Steps | `generators/steps_builder.py` | ✅ | 从 DAG 生成路径 + 异常分支 |
| 3C GT | `generators/golden_builder.py` | ✅ | 只吃材料 + 验证器，**拿不到 Rubric** |
| 3D Rubric | `generators/rubric_builder.py` | ✅ | 4 层结构，**拿不到 GT** |
| 4 独立验证 | `financial_verifiers/` | ✅ | 5 个确定性验证器（Decimal 精确） |
| 4.5 Rubric QA | `evaluation/rubric_qa.py` | ✅ | 6 个检查器 |
| 4.6 变异测试 | `evaluation/mutation_test.py` | ✅ | 改一个数，判分必须翻 |
| 5 盲测记录 | `evaluation/blind_evaluation.py` | ✅（记录层） | run schema + 题面哈希绑定；**执行仍外部** |
| 5.5 难度预检 | `evaluation/difficulty_preflight.py` | ✅ | 门槛规则可配置，两种读法都记账 |
| 6 提交门禁 | `quality_gates/xpert_readiness.py` | ✅ | 六材料 + 12 项 + 闸门汇总 |

## 三处最关键的实现决定

### 1. GT 与 Rubric 的输入集合必须不相交

```python
# generators/isolation.py
assert_disjoint(
    gt_inputs=["materials", "verifiers"],          # 允许
    rubric_inputs=["prompt", "materials", "rules"], # 允许
)
# 一旦有人让 rubric 读 GT，或让 GT 读 rubric，直接抛 IsolationError
```

`golden_builder` 与 `rubric_builder` 各自声明 `declared_inputs`，运行时被 `isolation` 校验并签发回执（含输入哈希）。
回执进 `artifacts/`，任何人可以核对"这份 GT 是在看不到 Rubric 的情况下生成的"。

### 2. Rubric 从"题目要求 + 专业规则"抽，不从答案反推

`rubric_builder` 的输入只有题面交付要求、材料字段清单、口径文件。抽考点的规则：
一个交付要求 → 一条考点；一条考点只查一件事；每条必须能指向材料里的字段或记录编号；
每条自带 `tolerance` 与 `accepted_alternatives`（对应改造建议里"合理替代"的要求）。

### 3. 难度门槛做成数据，不写死在代码里

```yaml
# registry/difficulty_rule.yaml
judge_max: 50
steps_min: 50
time_min_seconds: 2400
combine: any_two        # 步数≥50 或 时长>2400 秒（当前书面口径）
```

改造建议里写的是"Judge ≤50 且步数 ≥50 两项同时满足"，与仓库此前记录的
"步数 ≥50 **或** 时长 > 2400 秒"**不一致**。V2 不替项目方选边：
规则是配置，`combine` 可切 `all` / `any_two` / `any`，预检输出**两种读法各自的结论**，
并把所用规则版本写进记录。争议时要能复现"当时按哪条判的"。

## 金融复杂度：五种机制落到 DAG 上

不靠附件数量堆难度，靠**前置判断改变会传播到下游结果**：

| 机制 | 在 DAG 里的形态 |
|---|---|
| D1 多源证据冲突 | 同一事实的多条证据边，指向同一个判断节点 |
| D2 时间与状态依赖 | 判断节点带 `time_dependent=True`，状态变更产生新的边 |
| D3 多约束优化 | 一个决策节点挂多个约束节点（资本/预算/授权/时限） |
| D4 口径敏感性 | 节点带 `sensitive_to`，口径不同则下游分支不同 |
| D5 下游执行责任 | 终态节点必须产出"谁批准/何时执行/什么条件停止" |

`task_architect/complexity.py` 把这些数成 E/C/T/D/S/V/A，**只做内部排序与选题参考**，
不写进题面、不宣称达到平台门槛。

## 路线图

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0 | 案例真实性登记、PII、三级 Skill 唯一性、区分度、查重 | ✅ 本分支 |
| P1 | Prompt / Steps / GT / Rubric 四段拆分 + 隔离回执 | ✅ 本分支 |
| P2 | 确定性验证器 + Rubric QA + 变异测试 | ✅ 本分支 |
| P3 | 豆包真实运行、错误证据提取、独立评分 | ⏳ 执行层外部，本分支只给 schema 与校验 |
| P4 | 六材料分别输出、附件槽位分类、文件一致性、提交清单 | ✅ 门禁层；打包仍用 V1 `pack` |

## 与 V1 的关系

- V1 的 `util` / `scan` / `pack` / `cases/` 复用，不重写。
- V1 的 `verify_pack.py` 保留但降级为"题包自洽检查"，V2 用 `quality_gates/xpert_readiness.py`
  做外部事实驱动的门禁（材料行数、GT 表数、运行记录绑定、隔离回执）。
- `packs/7689005313907642138` 留在 main 作对照，V2 不修改它。

## 下一步（需要你定的两件事）

1. **难度口径**：`combine` 用 `any_two`（现行书面口径，46/100 + 2916 秒即达标）
   还是 `all`（Judge ≤50 且步数 ≥50，则 2138 的 22 步不达标）？V2 已按 11.4 定稿：`combine: all`（两项必须同时满足），旧 `any_two` 仅作历史读法并列展示。
2. **第一个 V2 试点**：建议 7689005313907642138（材料齐、48 格、考点已冻结），
   用原件重跑 3C/3D 并出隔离回执，作为 V2 的回归基准。
