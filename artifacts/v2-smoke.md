# V2 冒烟报告

八阶段各跑一次，全部为真实计算，无占位。

## Stage 0 · 案例登记与真实性门禁

- `7682696205114576686`：PASS  PII=0（high=0）
- `7682696962462060297`：PASS  PII=0（high=0）
- `7682697017533435698`：PASS  PII=0（high=0）
- `7689004886126038822`：BLOCK [('A4', 'public 案例缺少 released_at')] PII=0（high=0）
- `7689004928191450926`：PASS  PII=0（high=0）
- `7689005303455141641`：PASS  PII=0（high=0）
- `7689005308652818202`：PASS  PII=0（high=0）
- `7689005313907642138`：PASS  PII=0（high=0）
- `7699775475468144393`：PASS  PII=0（high=0）
- `ccb-vendor-tpr-2026`：BLOCK [('A5', 'synthetic 案例未声明已标注，或题面未写合成说明')] PII=0（high=0）

登记 8 个，拦截 2 个。

## Stage 1 · 三级 Skill 匹配

- 0.481  信息科技外包风险管理 / 第三方供应商技术风险定级与处置意见编制  platform=False blocked=False 
- 0.333  基金清算 / 核验清算资产清单  platform=True blocked=True 三级 Skill 已被占用
- 0.333  股权融资项目 / 核验股权沿革  platform=True blocked=True 三级 Skill 已被占用
- 0.308  基金估值与净值 / 核验估值日持仓数量  platform=True blocked=True 三级 Skill 已被占用

选中：**信息科技外包风险管理 / 第三方供应商技术风险定级与处置意见编制**

## Stage 2 · 决策链与复杂度

- E=6 C=3 T=1 D=1 S=2 V=3 A=1 最大传播度=2
- 复杂度自检：通过
- 说明：指标只做选题排序，不进题面、不作门槛。

## Stage 3D · 独立抽考点（不读 GT）

- 从题面抽出 12 条考点，权重合计 **100**
- 层级分布：{'L1': 9, 'L3': 3}
- 有证据锚点：11/12
- 隔离：GT 输入 {materials, verifiers} 与 Rubric 输入 {prompt, materials, rules} 不共享对方产物 ✅

## Stage 4.5 · Rubric QA 六检查器

- fail=10 warn=12
  - [fail] evidence: R1 无证据锚点
  - [warn] alternative: R1 未登记合理替代写法，可能误杀等价答案
  - [warn] alternative: R2 未登记合理替代写法，可能误杀等价答案
  - [warn] alternative: R3 未登记合理替代写法，可能误杀等价答案
  - [warn] alternative: R4 未登记合理替代写法，可能误杀等价答案
  - [warn] alternative: R5 未登记合理替代写法，可能误杀等价答案
  - [warn] alternative: R6 未登记合理替代写法，可能误杀等价答案
  - [warn] alternative: R7 未登记合理替代写法，可能误杀等价答案

## Stage 4 · 确定性验证器

- [PASS] 次级债按期限折算后合计: 期望 700 实得 700.0000 容差 0.01 次级债明细#剩余期限
- [PASS] 净资本: 期望 5580 实得 5580.0000 容差 0.01 净资产−扣减+合格次级债
- 结论：全部通过

## Stage 4.6 · 变异测试（改一个数必须翻分）

- net_capital: 基线 100 → 超容差 40 / 容差内 100 PASS
- nav: 基线 100 → 超容差 60 / 容差内 100 PASS

## Stage 5.5 · 难度预检（两种读法同时输出）

- 规则：FSF-DIFF-v1 combine=any_two
- 得分 46 ≤ 50：True；步数 22：False；时长 2916s：True
- 读法 A（any_two）：PASS；读法 B（all）：FAIL
- 采用 `any_two` → **PASS**
- 记录采信说明：46/100 与 48.6 分钟来自平台记录，非本仓库实测。

## Stage 6 · 提交门禁（外部事实驱动）

- 结论：NOT READY（3 个 blocker）
  - 隔离回执·gt: 缺回执：无法证明生成时未读取对方产物
  - 隔离回执·rubric: 缺回执：无法证明生成时未读取对方产物
  - source_type 非空: 

---

本报告由 `tools/v2_smoke.py` 生成；数字全部来自当场计算。