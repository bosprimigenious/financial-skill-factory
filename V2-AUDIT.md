# V1 代码审计（改造前基线）

审计对象：`src/fsf/`（615 行）、`tools/verify_pack.py`（171 行）、`cases/ccb-vendor-tpr-2026/build_case.py`（683 行）、`tests/`（155 行）。
审计时点：V1 已公开、9 个实例入库、1 个成品题包。

## 一、V1 实际有什么（按能力列，不按文件）

| 能力 | 实现位置 | 可靠度 | 说明 |
|---|---|---|---|
| 案例加载（case.yaml/json） | `util.parse_minimal_yaml` / `load_case` | 中 | 自写 YAML 解析器，只支持一层列表；`case.json` 是更稳的退路 |
| 材料盘点 + sha256 | `ingest.py` | 高 | 纯 I/O，无业务假设 |
| 材料体检 | `scan.py`（170 行） | 中 | 检查缺文件、扩展名白名单、空文件、`checks` 断言；`verdict=PASS/WARN/FAIL` |
| 六槽位骨架 | `pack.py` | 高 | 目录与模板落位；`source_type=synthetic` 直接拒包 |
| 题包机器校验 | `verify_pack.py` | **低** | 见下节，大量断言是"自证" |
| 材料+GT 单一事实源 | `build_case.py` | 高 | 48 格断言逐格对齐冻结考点，改数据即报错 |

## 二、审计结论：V1 的三个结构性问题

### P0-1 `verify_pack.py` 有 41/54 项是自证，不是独立验收

54 项里只有 13 项真的在验外部事实：

- 真外部：材料 12 件存在 + 行数（12 项）、GT xlsx 存在 + 5 表齐 + D1 48 格（3 项）
- 自证：权重和=100（读我自己写的 rubric）、"GT 含 48 格分布"（查我自己写的字符串）、
  "失败六条=54"（按我自己的权重表算）、门槛 PASS（读我自己写的 meta）

后果：题包可以**内部完全自洽而整体错误**——上一轮 `MATERIAL-DIVERGENCE.md` 就是这个后果：
54/54 PASS 的包，材料其实不是平台原件。自证永远发现不了这件事，只有外部原件能发现。

### P0-2 GT 与 Rubric 由同一份输入、同一次运行产出，等于自我认证

`pack.py` 只做模板渲染：`03_private_review/GT/golden_response.md` 与
`02_platform_fields/expert_rubric.csv` 来自 `src/fsf/templates/`，两者没有任何交叉校验，
也**没有隔离机制**——谁都能读另一份。`build_case.py` 更彻底：一份事实表同时算出
材料和 GT，断言再严也只是"我按我的规则算出了我期待的答案"。

这正是改造建议里"不能让同一个 Agent 出题、写答案、写评分标准、证明自己合格"的具体形态。

### P0-3 没有难度预检与运行记录，难度靠事后争议

`scan.py` 完全不涉及难度；`00_meta.json` 里的 46/100、48.6 分钟是**手抄进 meta 的**，
没有运行记录 schema，没有"哪个版本的题面配哪次运行"的绑定。返修一次就分不清分数的出处。

## 三、V1 值得保留的部分（不要重写）

| 模块 | 保留理由 |
|---|---|
| `util`（路径、sha256、case 加载） | 无业务假设，V2 直接复用 |
| `scan`（材料体检） | 材料缺件/空件/白名单是真实闸门，V2 作为 G2 的一环继续用 |
| `pack`（六槽位 + synthetic 拒包） | 槽位约定与平台提交六材料一致；拒包规则是对的 |
| `build_case`（单一事实源 + 逐格断言） | 断言方向正确，V2 把它降级为"Calculation GT 生成器"，不再兼任 Rubric |
| `cases/` 9 个实例 + `PROVENANCE.md` | 真实材料与 sha256 是 V2 的输入 |

## 四、与改造建议八阶段的差距

| Stage | V1 现状 | 差距 |
|---|---|---|
| 0 Case Registry | `case.json` + `PROVENANCE.md`（半手工） | 缺授权/真实性标签、缺门禁判定、缺 PII 扫描 |
| 1 Skill Mapper | 无（手工填 `l2_skill/level3_skill`） | 全缺 |
| 2 Task Architect | 无 | 缺决策链、依赖图、复杂度指标 E/C/T/D/S/V/A |
| 3A Prompt | 模板 | 模板不读决策链，容易"先写题面后找难度" |
| 3B Ideal Steps | 模板 | 同上 |
| 3C GT | 模板 + build_case | 无独立计算器，无隔离 |
| 3D Rubric | 模板 CSV | 无 4 层结构、无 6 个 QA 检查器、无变异测试 |
| 4 Independent Verify | 只有 `build_case` 断言 | 无金融专用验证器 |
| 5 Doubao Blind Eval | 无（手抄分数） | 缺运行记录 schema |
| 6 Xpert Gate | `verify_pack`（自证） | 需改为"外部事实驱动" |

## 五、改造边界（明确不做什么）

- **不重写** `util` / `scan` / `pack` / `cases/`。
- **不动** 已公开的 `packs/7689005313907642138`（V1 产物留作对照）。
- **不在 V2 里伪造豆包运行**：Stage 5 只落 schema 与记录校验，真实运行仍是外部动作。
- **不把指标当门槛**：E/C/T/D/S/V/A 只做内部排序，禁止写进题面或宣称达到二轮门槛。

## 六、审计判据

每条结论都能在仓库里指到位置：

- 自证项数 41/54：`tools/verify_pack.py` 逐项读自身产物，无外部输入。
- 无隔离：`generators/` 在 V1 不存在；`pack.py` 无交叉校验调用。
- 难度手抄：`packs/7689005313907642138/00_meta.json` 的 `measured` 块无 `run_id` / 无题面哈希。
