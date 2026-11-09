# INPUT_CONTRACT · 分析ETF折溢价与申赎套利机制

材料落 `inputs/`，命名 `{{序号}}_{{对象}}.{{ext}}`。逐件给出行数、主键、字段与单位。

| 文件 | 业务主键 | 必备字段 |
|---|---|---|
| `ETF_QUOTES.csv` | `fund+trade_date+ts` | `fund_code`, `trade_date`, `ts`, `bid`, `ask`, `last`, `volume` |
| `NAV_IOPV.csv` | `fund+trade_date+ts` | `fund_code`, `trade_date`, `ts`, `nav`, `iopv`, `nav_date` |
| `PCF_BASKET.csv` | `fund+trade_date` | `fund_code`, `trade_date`, `component`, `qty`, `cash_substitute`, `premium_ratio` |
| `FEES.csv` | `fund` | `fund_code`, `fee_type`, `rate`, `min_amount`, `note` |

## 通用约束

- 编码 UTF-8（含 BOM 亦可）；日期 ISO-8601 且注明时区；金额注明币种与精度。
- 空值必须区分 `UNKNOWN` / `NOT_OBSERVED` / `NOT_PROVEN` / `NOT_RUN`。
- 每份文件计算 SHA-256，写入 `04_EVIDENCE/SOURCE_REGISTER.csv`。
- **缺少任一必备字段即材料不合格**，先补材料，不讨论难度。
