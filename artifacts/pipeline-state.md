# 产线状态（tools/fsf_run.py 现场生成）

- 运行范围：10 个案例
- 占用集：8 个三级 Skill

| 案例 | intake | authenticity | skill | rubric | qa | mutation | difficulty | readiness |
|---|---|---|---|---|---|---|---|---|
| `7682696205114576686` | OK | OK | OK | **SKIP** | **SKIP** | **SKIP** | **SKIP** | **SKIP** |
| `7682696962462060297` | OK | OK | OK | **SKIP** | **SKIP** | **SKIP** | **SKIP** | **SKIP** |
| `7682697017533435698` | OK | OK | OK | **SKIP** | **SKIP** | **SKIP** | **SKIP** | **SKIP** |
| `7689004886126038822` | OK | **FAIL** | **FAIL** | **SKIP** | **SKIP** | **SKIP** | **SKIP** | **SKIP** |
| `7689004928191450926` | OK | OK | OK | **SKIP** | **SKIP** | **SKIP** | **SKIP** | **SKIP** |
| `7689005303455141641` | OK | OK | OK | **SKIP** | **SKIP** | **SKIP** | **SKIP** | **SKIP** |
| `7689005308652818202` | OK | OK | OK | **SKIP** | **SKIP** | **SKIP** | **SKIP** | **SKIP** |
| `7689005313907642138` | OK | OK | OK | OK | **FAIL** | **SKIP** | **SKIP** | **FAIL** |
| `7699775475468144393` | OK | OK | OK | **SKIP** | **SKIP** | **SKIP** | **SKIP** | **SKIP** |
| `ccb-vendor-tpr-2026` | OK | **FAIL** | OK | **SKIP** | **SKIP** | **SKIP** | **SKIP** | **SKIP** |

## 明细

### 7682696205114576686
- **intake** OK — 17 件材料，哈希一致
- **authenticity** OK — 7 条全过
- **skill** OK — 销售交易与经纪 / 复核成交分配与执行偏差
- **rubric** SKIP — 缺题面或材料字段
- **qa** SKIP — 无考点
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** SKIP — 尚未生成题包

### 7682696962462060297
- **intake** OK — 19 件材料，哈希一致
- **authenticity** OK — 7 条全过
- **skill** OK — 公司研究与财报分析 / 复核跨期收入确认与股份结算桥接
- **rubric** SKIP — 缺题面或材料字段
- **qa** SKIP — 无考点
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** SKIP — 尚未生成题包

### 7682697017533435698
- **intake** OK — 38 件材料，哈希一致
- **authenticity** OK — 7 条全过
- **skill** OK — 信息科技外包风险管理 / 第三方供应商技术风险定级与处置意见编制
- **rubric** SKIP — 缺题面或材料字段
- **qa** SKIP — 无考点
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** SKIP — 尚未生成题包

### 7689004886126038822
- **intake** OK — 5 件材料，哈希一致
- **authenticity** FAIL — A4:public 案例缺少 released_at
- **skill** FAIL — 候选三级 Skill 均已被占用：核验清算资产清单, 评估流动性缺口, 计提管理费
- **rubric** SKIP — 缺题面或材料字段
- **qa** SKIP — 无考点
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** SKIP — 尚未生成题包

### 7689004928191450926
- **intake** OK — 20 件材料，哈希一致
- **authenticity** OK — 7 条全过
- **skill** OK — 公司研究与财报分析 / 复核跨期收入确认与股份结算桥接
- **rubric** SKIP — 缺题面或材料字段
- **qa** SKIP — 无考点
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** SKIP — 尚未生成题包

### 7689005303455141641
- **intake** OK — 18 件材料，哈希一致
- **authenticity** OK — 7 条全过
- **skill** OK — 公司研究与财报分析 / 复核跨期收入确认与股份结算桥接
- **rubric** SKIP — 缺题面或材料字段
- **qa** SKIP — 无考点
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** SKIP — 尚未生成题包

### 7689005308652818202
- **intake** OK — 16 件材料，哈希一致
- **authenticity** OK — 7 条全过
- **skill** OK — 信息科技外包风险管理 / 第三方供应商技术风险定级与处置意见编制
- **rubric** SKIP — 缺题面或材料字段
- **qa** SKIP — 无考点
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** SKIP — 尚未生成题包

### 7689005313907642138
- **intake** OK — 12 件材料，哈希一致
- **authenticity** OK — 7 条全过
- **skill** OK — 公司研究与财报分析 / 复核跨期收入确认与股份结算桥接
- **rubric** OK — 12 条 / 合计 100
- **qa** FAIL — fail=10 warn=12
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** FAIL — 3 个 blocker

### 7699775475468144393
- **intake** OK — 10 件材料，哈希一致
- **authenticity** OK — 7 条全过
- **skill** OK — 公司研究与财报分析 / 复核跨期收入确认与股份结算桥接
- **rubric** SKIP — 缺题面或材料字段
- **qa** SKIP — 无考点
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** SKIP — 尚未生成题包

### ccb-vendor-tpr-2026
- **intake** OK — 0 件材料，哈希一致
- **authenticity** FAIL — A5:synthetic 案例未声明已标注，或题面未写合成说明; A7:未提供 level3_skill
- **skill** OK — 信息科技外包风险管理 / 第三方供应商技术风险定级与处置意见编制
- **rubric** SKIP — 缺题面或材料字段
- **qa** SKIP — 无考点
- **mutation** SKIP — 缺 mutation_expected.json
- **difficulty** SKIP — 无运行记录（UNTESTED，不得当作达标）
- **readiness** SKIP — 尚未生成题包
