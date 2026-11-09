# INPUT_CONTRACT · 归因个人组合收益与基准偏离

材料落 `inputs/`，命名 `{{序号}}_{{对象}}.{{ext}}`。逐件给出行数、主键、字段与单位。

| 文件 | 业务主键 | 必备字段 |
|---|---|---|
| `POSITIONS.csv` | `account+symbol+date` | `account`, `symbol`, `date`, `qty`, `price`, `market_value`, `currency` |
| `TRANSACTIONS.csv` | `txn_id` | `txn_id`, `account`, `symbol`, `trade_date`, `side`, `qty`, `price`, `fee`, `fx_rate` |
| `BENCHMARK.csv` | `benchmark+date` | `benchmark`, `date`, `return`, `weight_scheme` |

## 通用约束

- 编码 UTF-8（含 BOM 亦可）；日期 ISO-8601 且注明时区；金额注明币种与精度。
- 空值必须区分 `UNKNOWN` / `NOT_OBSERVED` / `NOT_PROVEN` / `NOT_RUN`。
- 每份文件计算 SHA-256，写入 `04_EVIDENCE/SOURCE_REGISTER.csv`。
- **缺少任一必备字段即材料不合格**，先补材料，不讨论难度。
