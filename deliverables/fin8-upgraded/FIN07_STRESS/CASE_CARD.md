# FIN07_STRESS

- Industry: 金融
- Platform task ID: 7705054469567057727
- L2: 压力测试与风险限额
- L3: 设计压力情景
- Professional domain: 投资组合风险因子压力情景设计与限额评估
- Status: SCAFFOLD_ONLY

## Business objects
- 风险因子
- 资产敞口
- 组合
- 风险限额
- 历史压力事件
- 相关结构
- 估值模型

## Genuine input classes
- 组合风险敞口
- 风险因子时间序列
- 限额政策
- 历史事件
- 模型参数
- 已批准情景方法

## Professional decisions
- 选择具有经济机制的风险因子
- 设计单因子和联合情景
- 处理相关性变化和非线性
- 评估基准/压力结果与限额使用
- 确定管理行动和升级条件

## Failure modes to test (derive from real evidence)
- 随意设定冲击幅度
- 忽略相关性在压力期变化
- 重复计算风险敞口
- 使用过期限额
- 把未运行模型写成已验证

No real case, data, authorization, GT, model run or platform acceptance is implied by this scaffold.
