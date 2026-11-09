# FIN02_PRICE_VOLUME

- Industry: 金融
- Platform task ID: 7705055634240196361
- L2: 市场异动归因与复盘
- L3: 解读量价筹码与资金行为
- Professional domain: 证券市场量价结构与资金行为复盘
- Status: SCAFFOLD_ONLY

## Business objects
- 证券
- 交易日
- OHLCV
- 换手率
- 流通股本
- 资金流口径
- 事件窗口
- 复权因子

## Genuine input classes
- 行情数据
- 证券主数据
- 股本与流通股数据
- 公司行动
- 资金流数据及方法说明
- 事件时间线

## Professional decisions
- 定义异常窗口和基准期
- 区分价格变化、成交活跃度和可观测资金流
- 判断信号是否由公司行动或样本选择造成
- 比较市场/行业基准
- 给出多种可证伪解释

## Failure modes to test (derive from real evidence)
- 把资金流估算写成真实主力行为
- 忽略复权
- 选择性窗口
- 将相关性解释为因果
- 把流通股本和总股本混用

No real case, data, authorization, GT, model run or platform acceptance is implied by this scaffold.
