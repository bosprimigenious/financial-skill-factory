# 材料契约（4 件）

真实公开数据接入后，按此契约落盘 `materials/`，缺字段即材料不合格。

## M1 数据源目录.csv
`source_id, source_name, vendor, freq, history_start, license, pit_flag, coverage_note`
- `pit_flag`：发布日是否可回溯（TRUE/FALSE），不是"数据里有日期"就算 PIT
- `license`：商用/研究/仅展示，缺席视为不可用

## M2 观测数据.csv
`source_id, entity, ts, field, value, unit, revision_no, released_at`
- `ts` 观测日与 `released_at` 发布日必须分列（前视判定的唯一依据）
- `revision_no`：同一观测的修订版本，**不得只保留最新版**

## M3 实体映射.csv
`entity, ticker, name, exchange, valid_from, valid_to, mapping_rule`
- 必须覆盖代码复用/借壳的一对多；`valid_to` 为空表示仍有效

## M4 口径说明.md
指标定义、停牌与节假日处理、复权方式、时区、缺失值语义（UNKNOWN/NOT_OBSERVED/NOT_PROVEN）。
