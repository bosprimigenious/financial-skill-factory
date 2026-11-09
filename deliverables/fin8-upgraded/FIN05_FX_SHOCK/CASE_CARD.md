# FIN05_FX_SHOCK

- Industry: 金融
- Platform task ID: 7705055005066317587
- L2: 宏观与市场策略研究
- L3: 评估汇率冲击影响
- Professional domain: 汇率变动对资产负债及现金流的风险传导
- Status: SCAFFOLD_ONLY

## Business objects
- 币种敞口
- 外币资产负债
- 收入成本
- 现金流
- 远期/掉期/期权套保
- 汇率情景

## Genuine input classes
- 外币敞口表
- 现金流期限表
- 套保合约
- 历史汇率与定盘价
- 宏观情景依据
- 主体财务口径

## Professional decisions
- 区分交易、折算和经济敞口
- 按期限匹配套保
- 量化直接和间接影响
- 处理自然对冲
- 比较冲击情景及敏感性

## Failure modes to test (derive from real evidence)
- 币种方向颠倒
- 把名义套保额当完全抵消
- 忽略期限错配
- 将折算损益和现金流损益混为一谈
- 用当前汇率回填历史

No real case, data, authorization, GT, model run or platform acceptance is implied by this scaffold.
