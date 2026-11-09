# INPUT_CONTRACT · 评估汇率冲击影响

材料落 `inputs/`，命名 `{{序号}}_{{对象}}.{{ext}}`。逐件给出行数、主键、字段与单位。

| 文件 | 业务主键 | 必备字段 |
|---|---|---|
| `FX_EXPOSURE.csv` | `entity+currency` | `entity`, `currency`, `exposure_amount`, `exposure_type`, `as_of` |
| `CASHFLOWS.csv` | `flow_id` | `flow_id`, `entity`, `currency`, `due_date`, `amount`, `direction` |
| `HEDGES.csv` | `hedge_id` | `hedge_id`, `currency`, `notional`, `strike`, `maturity`, `instrument` |

## 通用约束

- 编码 UTF-8（含 BOM 亦可）；日期 ISO-8601 且注明时区；金额注明币种与精度。
- 空值必须区分 `UNKNOWN` / `NOT_OBSERVED` / `NOT_PROVEN` / `NOT_RUN`。
- 每份文件计算 SHA-256，写入 `04_EVIDENCE/SOURCE_REGISTER.csv`。
- **缺少任一必备字段即材料不合格**，先补材料，不讨论难度。
