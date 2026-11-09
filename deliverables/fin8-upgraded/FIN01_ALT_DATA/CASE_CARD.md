# FIN01_ALT_DATA

- Industry: 金融
- Platform task ID: 7705055555161788179
- L2: 市场数据与信息查询
- L3: 查询行业高频与另类数据
- Professional domain: 金融另类数据准入、谱系与研究可用性
- Status: SCAFFOLD_ONLY

## Business objects
- 数据源
- 数据集版本
- 实体映射
- 观测值
- 事件时间
- 发布时间
- 许可与再分发边界

## Genuine input classes
- 数据源目录
- 数据字典
- 真实观测数据
- 实体映射表
- 数据质量报告
- 许可与授权记录

## Professional decisions
- 判定数据源是否适合研究目的
- 识别事件时间与发布时间差异
- 审查实体映射与覆盖率
- 识别修订、缺失、延迟和幸存者偏差
- 区分可研究、可商业使用与可再分发

## Failure modes to test (derive from real evidence)
- 把公开可访问等同于可再分发
- 把发布时间当事件时间
- 忽略映射版本
- 把缺失当零
- 把数据延迟误判为真实市场信号

No real case, data, authorization, GT, model run or platform acceptance is implied by this scaffold.
