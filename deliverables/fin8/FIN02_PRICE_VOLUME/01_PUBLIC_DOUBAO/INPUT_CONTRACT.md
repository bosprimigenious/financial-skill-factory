# INPUT_CONTRACT · 解读量价筹码与资金行为

材料落 `inputs/`，命名 `{{序号}}_{{对象}}.{{ext}}`。逐件给出行数、主键、字段与单位。

| 文件 | 业务主键 | 必备字段 |
|---|---|---|
| `OHLCV.csv` | `symbol+trade_date` | `symbol`, `trade_date`, `open`, `high`, `low`, `close`, `volume`, `amount`, `adj_factor` |
| `FLOAT.csv` | `symbol+trade_date` | `symbol`, `trade_date`, `float_shares`, `holder_concentration`, `pledge_ratio` |
| `FLOW.csv` | `symbol+trade_date+channel` | `symbol`, `trade_date`, `channel`, `net_inflow`, `large_order_ratio`, `block_trade_flag` |
| `EVENT_LOG.csv` | `event_id` | `event_id`, `symbol`, `event_date`, `event_type`, `source`, `verified` |

## 通用约束

- 编码 UTF-8（含 BOM 亦可）；日期 ISO-8601 且注明时区；金额注明币种与精度。
- 空值必须区分 `UNKNOWN` / `NOT_OBSERVED` / `NOT_PROVEN` / `NOT_RUN`。
- 每份文件计算 SHA-256，写入 `04_EVIDENCE/SOURCE_REGISTER.csv`。
- **缺少任一必备字段即材料不合格**，先补材料，不讨论难度。
