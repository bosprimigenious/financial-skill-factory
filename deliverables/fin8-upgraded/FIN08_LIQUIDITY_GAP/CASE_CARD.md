# FIN08_LIQUIDITY_GAP

- Industry: 金融
- Platform task ID: 7705055005065203475
- L2: 投资风险管理
- L3: 评估流动性缺口
- Professional domain: 投资组合期限桶流动性缺口与资产可用性分析
- Status: SCAFFOLD_ONLY

## Business objects
- 现金流入
- 现金流出
- 资产变现
- 负债到期
- 抵质押/冻结
- 期限桶
- 流动性折扣

## Genuine input classes
- 资产负债现金流
- 资产持仓与市场价值
- 结算周期
- 抵质押状态
- 历史赎回/融资行为
- 流动性政策和压力假设

## Professional decisions
- 按期限桶匹配流入流出
- 判断资产是否能在缺口前变现
- 扣除受限资产和合理折价
- 计算基准与压力缺口
- 提出可执行的流动性缓释措施

## Failure modes to test (derive from real evidence)
- 账面价值当作可用现金
- 忽略结算周期
- 遗漏或有流出
- 重复计入抵押资产
- 把负缺口净额跨期限抵消

No real case, data, authorization, GT, model run or platform acceptance is implied by this scaffold.
