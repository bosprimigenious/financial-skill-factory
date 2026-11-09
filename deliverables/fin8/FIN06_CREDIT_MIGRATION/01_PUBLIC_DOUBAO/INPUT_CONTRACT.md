# INPUT_CONTRACT · 识别信用评级迁移风险

材料落 `inputs/`，命名 `{{序号}}_{{对象}}.{{ext}}`。逐件给出行数、主键、字段与单位。

| 文件 | 业务主键 | 必备字段 |
|---|---|---|
| `ISSUER.csv` | `issuer_id` | `issuer_id`, `name`, `industry`, `region`, `external_rating`, `outlook` |
| `RATING_HISTORY.csv` | `issuer_id+date` | `issuer_id`, `date`, `rating`, `agency`, `action` |
| `FINANCIALS.csv` | `issuer_id+period` | `issuer_id`, `period`, `revenue`, `ebitda`, `debt`, `interest`, `cash` |

## 通用约束

- 编码 UTF-8（含 BOM 亦可）；日期 ISO-8601 且注明时区；金额注明币种与精度。
- 空值必须区分 `UNKNOWN` / `NOT_OBSERVED` / `NOT_PROVEN` / `NOT_RUN`。
- 每份文件计算 SHA-256，写入 `04_EVIDENCE/SOURCE_REGISTER.csv`。
- **缺少任一必备字段即材料不合格**，先补材料，不讨论难度。
