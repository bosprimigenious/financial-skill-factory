# cases/ — 真实案例目录契约

一个案例一个目录：

```text
cases/<case-id>/
  case.yaml
  materials/            真实、脱敏的输入材料（xlsx/csv/pdf/docx/图片）
```

## case.yaml

```yaml
id: CASE-001
title: 基金估值日持仓数量三方核对
platform_task_id: "7705055496872939307"
industry: 金融
l2_skill: 基金估值与净值
level3_skill: 核验估值日持仓数量
source_type: real          # real | public | synthetic
as_of: "2026-09-30"        # 数据截止时点
currency: CNY
disclosure_note: "已脱敏：客户名称替换为 X 基金，账号后四位保留"
required_files:
  - materials/valuation.xlsx
  - materials/broker_statement.xlsx
  - materials/trades.csv
  - materials/corporate_actions.pdf
```

## 规则

- `source_type: synthetic` 仅用于工程自测，禁止进入 `packs/`。
- `required_files` 会由 `fsf check` 逐项校验存在性。
- 所有材料先脱敏；原文件名可保留，但内容不得含个人敏感信息、账号全号、客户身份。
- 一个案例只对应一个三级 Skill（平台唯一性）。
