# FIN03_ETF_ARB

- Industry: 金融
- Platform task ID: 7705055652846309139
- L2: 基金与ETF研究评价
- L3: 分析ETF折溢价与申赎套利机制
- Professional domain: ETF折溢价监测与申赎套利经济性
- Status: SCAFFOLD_ONLY

## Business objects
- ETF份额
- 二级市场价格
- NAV/IOPV
- PCF申赎篮子
- 现金替代
- 申赎单位
- 交易费用
- 交收周期

## Genuine input classes
- 交易所行情
- 基金NAV/IOPV
- 申赎清单PCF
- 基金合同/招募说明书
- 费率与现金替代规则
- 交易日历与结算规则

## Professional decisions
- 核验价格与净值时间戳
- 逐成分核对申赎篮子
- 计算可执行套利毛利和净利
- 识别停牌、限购、现金替代和交收约束
- 区分理论偏离与可实现收益

## Failure modes to test (derive from real evidence)
- 用过期NAV计算折溢价
- 忽略现金替代溢价
- 遗漏申赎费用
- 将理论价差当无风险收益
- 忽略交收时点

No real case, data, authorization, GT, model run or platform acceptance is implied by this scaffold.
