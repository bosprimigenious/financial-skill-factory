# RUBRIC_RULES · 查询行业高频与另类数据

## 两套 Rubric 不混用

| 文件 | 用途 | 计分 |
|---|---|---|
| `PLATFORM_EXPERT_RUBRIC.template.csv` | Xpert 平台专家 Rubric（11.4 字段） | 平台百分制 |
| `INTERNAL_GRADER_20x5.template.csv` | 内部评测（C01–C19 ＋ C20 人工） | 95 ＋ 5 |
| `HIDDEN_DIFFICULTY_MAP.template.csv` | 隐藏难点 → 考点的映射 | 不入分 |
| `04_EVIDENCE/C20_REVIEW.csv` | 专家人工独立评审留痕 | 5 |

**内部 20×5 不能替代平台 Rubric**，两者分别维护、分别冻结。

## 11.4 平台 Rubric 要求

- 必需项＋负向项合计 5–12 条；复杂任务可到 15 条以上，但须给复杂度依据。
- 加分项最多 2 条，不计入上述条数，**不得作为 Gate**。
- Gate 候选最多 3 条。
- 每条必须写：类型、核心判分点、达标标准、专业判断说明、依据来源与位置、
  数值与容差、合理替代。
- 一条只查一件事；禁止"考虑了 XX"这类灰度表述。
- 数值型必须给精度与容差；开放项必须给可接受替代。

## 生成方式

正式 Rubric 由 `generators/rubric_builder.py` 从题面交付要求独立抽取
（不读 GT），再用 `evaluation/rubric_qa.py` 六检查器过一遍。
