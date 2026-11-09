# FIN06_CREDIT_MIGRATION

- Industry: 金融
- Platform task ID: 7705055524749086518
- L2: 信用与固定收益研究
- L3: 识别信用评级迁移风险
- Professional domain: 发行人评级迁移与固定收益敞口风险
- Status: SCAFFOLD_ONLY

## Business objects
- 发行人
- 评级机构
- 评级级别
- 展望/观察
- 评级生效日
- 债券敞口
- 违约事件

## Genuine input classes
- 发行人主数据
- 评级历史
- 评级方法版本
- 财务报表
- 债券持仓及到期结构
- 违约事件记录

## Professional decisions
- 标准化不同评级机构尺度
- 构建迁移矩阵
- 区分评级观察与正式迁移
- 分析主体财务驱动
- 量化组合敞口迁移影响

## Failure modes to test (derive from real evidence)
- 把展望负面当正式降级
- 跨机构评级直接混合
- 忽略评级生效日
- 将评级迁移率等同违约概率
- 忽略退市/缺失样本

No real case, data, authorization, GT, model run or platform acceptance is implied by this scaffold.
