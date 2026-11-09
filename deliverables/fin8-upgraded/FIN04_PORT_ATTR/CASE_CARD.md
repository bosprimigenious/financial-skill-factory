# FIN04_PORT_ATTR

- Industry: 金融
- Platform task ID: 7705055555161820947
- L2: 持仓诊断与投资决策辅助
- L3: 归因个人组合收益与基准偏离
- Professional domain: 投资组合收益核算与主动收益归因
- Status: SCAFFOLD_ONLY

## Business objects
- 组合
- 证券持仓
- 交易
- 现金流
- 费用
- 基准权重
- 估值价格
- 收益期间

## Genuine input classes
- 期初期末持仓
- 交易流水
- 现金流
- 费用
- 基准成分权重和收益
- 估值价格与汇率

## Professional decisions
- 选择适用收益率方法
- 处理外部现金流和费用
- 统一组合与基准期间
- 分解资产配置、证券选择及交互效应
- 解释无法归因部分

## Failure modes to test (derive from real evidence)
- 混用时间加权和资金加权收益
- 遗漏现金流
- 基准成分错期
- 重复计算费用
- 归因分项不等于主动收益却不解释

No real case, data, authorization, GT, model run or platform acceptance is implied by this scaffold.
