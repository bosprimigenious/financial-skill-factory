# INPUT_CONTRACT · 查询行业高频与另类数据

材料落 `inputs/`，命名 `{{序号}}_{{对象}}.{{ext}}`。逐件给出行数、主键、字段与单位。

| 文件 | 业务主键 | 必备字段 |
|---|---|---|
| `SOURCE_CATALOG.csv` | `source_id` | `source_id`, `source_name`, `variant`, `freq`, `history_start`, `license`, `has_pit`, `coverage_note` |
| `OBSERVATIONS.csv` | `source_id+entity+ts` | `source_id`, `entity`, `ts`, `field`, `value`, `unit`, `revision_no` |
| `ENTITY_MAPPING.csv` | `entity` | `entity`, `ticker`, `name`, `exchange`, `valid_from`, `valid_to`, `mapping_rule` |

## 通用约束

- 编码 UTF-8（含 BOM 亦可）；日期 ISO-8601 且注明时区；金额注明币种与精度。
- 空值必须区分 `UNKNOWN` / `NOT_OBSERVED` / `NOT_PROVEN` / `NOT_RUN`。
- 每份文件计算 SHA-256，写入 `04_EVIDENCE/SOURCE_REGISTER.csv`。
- **缺少任一必备字段即材料不合格**，先补材料，不讨论难度。
