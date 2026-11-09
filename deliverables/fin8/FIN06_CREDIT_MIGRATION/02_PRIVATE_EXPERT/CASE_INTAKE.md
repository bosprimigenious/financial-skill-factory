# CASE_INTAKE · 识别信用评级迁移风险

> 真实性门禁 A1–A7（与产线 `case_intake/authenticity_gate.py` 同规则）。任一不过即拒绝进入生成。

- [ ] A1 来源可定位（URL / 合同编号 / 台账编号）
- [ ] A2 source_type 合法（real / public / synthetic）
- [ ] A3 real 必须有授权与脱敏标记
- [ ] A4 public 必须有发布日
- [ ] A5 synthetic 必须在题面标注合成
- [ ] A6 材料内无高危 PII（身份证/银行卡/手机号）
- [ ] A7 三级 Skill `识别信用评级迁移风险` 未被占用

## 授权与脱敏记录

| 项 | 内容 |
|---|---|
| 材料提供方 | TODO |
| 授权方式 | TODO |
| 脱敏处理 | TODO |
| 业务时点 | TODO |
