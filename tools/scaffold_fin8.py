#!/usr/bin/env python3
"""金融八题：按既有六层隔离结构生成 8 个独立小包 + 1 个总包。

原则（写进脚本，不靠人记）：
  * 只生成**脚手架**，不生成任何业务数据、不写 Golden Response 内容。
  * 两套 Rubric 物理分离：平台 11.4 专家 Rubric 与内部 20×5 不混用。
  * 每包 23 个文件（不含 inputs/ 内的材料，材料由真实来源填充）。
  * G7 用 11.4：Judge ≤50 且 单轮步数 ≥50；时长只做评级。
  * 每个文件都进 MANIFEST.sha256；总包再对 8 个 ZIP 做 CRC 校验。

用法：
  python3 tools/scaffold_fin8.py            # 生成到 deliverables/fin8/
  python3 tools/scaffold_fin8.py --verify   # 生成后立即自检
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables" / "fin8"

# ---------------------------------------------------------------- 八题配置
TASKS = [
    dict(
        code="FIN01", slug="ALT_DATA", auto="01 另类数据研究",
        l2="市场数据与信息查询", l3="查询行业高频与另类数据",
        platform="7705055555161788179", prio="优先试产",
        use="为因子研究确定可用数据源与特征口径，决定哪些字段进模型",
        cost="源选错或实体映射错，会让整条因子链在回测里表现为虚假 alpha",
        inputs=[("SOURCE_CATALOG", "source_id", ["source_id", "source_name", "variant", "freq", "history_start", "license", "has_pit", "coverage_note"]),
                ("OBSERVATIONS", "source_id+entity+ts", ["source_id", "entity", "ts", "field", "value", "unit", "revision_no"]),
                ("ENTITY_MAPPING", "entity", ["entity", "ticker", "name", "exchange", "valid_from", "valid_to", "mapping_rule"])],
        outputs=["D1 SOURCE_ASSESSMENT（逐源评估：可得性/时点真实性/覆盖率/实体一致性）",
                 "D2 FEATURE_DICTIONARY（逐字段：定义/单位/频率/滞后/前视风险）",
                 "D3 拒绝源清单与理由", "D4 口径与缺口登记"],
        chain=["源可得性", "时点真实性(point-in-time)", "实体映射", "字段前视风险", "特征入模决定"],
        difficulties=[("材料冲突", "同一指标两个源口径不同（复权/未复权、含停牌/不含）", "D1"),
                      ("时点误判", "快照版数据被当成 PIT 数据，回测偷看未来", "D2"),
                      ("实体错配", "代码复用与借壳导致 ticker→entity 一对多", "D3"),
                      ("顺手方法失效", "按覆盖率排序选源，忽略更新频率与许可证", "D1"),
                      ("假异常", "缺失被当作 0，覆盖率被高估", "D4")],
        params=["PIT 口径（发布日期 vs 观察日）", "实体映射有效期", "缺失值语义（UNKNOWN/NOT_OBSERVED）", "复权方式"],
        errors=["用最新快照回测", "把 NOT_PROVEN 当 0", "跨交易所代码未做映射"],
    ),
    dict(
        code="FIN02", slug="PRICE_VOLUME", auto="02 量价与资金行为",
        l2="市场异动归因与复盘", l3="解读量价筹码与资金行为",
        platform="7705055634240196361", prio="优先试产",
        use="判断异动是资金驱动还是事件驱动，决定是否调整仓位与风控阈值",
        cost="归因错会把一次性事件当趋势，导致追高或误砍",
        inputs=[("OHLCV", "symbol+trade_date", ["symbol", "trade_date", "open", "high", "low", "close", "volume", "amount", "adj_factor"]),
                ("FLOAT", "symbol+trade_date", ["symbol", "trade_date", "float_shares", "holder_concentration", "pledge_ratio"]),
                ("FLOW", "symbol+trade_date+channel", ["symbol", "trade_date", "channel", "net_inflow", "large_order_ratio", "block_trade_flag"]),
                ("EVENT_LOG", "event_id", ["event_id", "symbol", "event_date", "event_type", "source", "verified"])],
        outputs=["D1 EVENT_WINDOW（逐事件窗口与剔除口径）", "D2 PRICE_VOLUME_DECOMPOSITION（量价分解：价格/成交/换手）",
                 "D3 资金分渠道归因与残差", "D4 口径与缺口登记"],
        chain=["事件识别", "窗口切分与剔除", "量价分解", "资金归因", "异常归因结论"],
        difficulties=[("口径不一致", "成交额口径（含大宗/不含）与换手率分母（自由流通 vs 总股本）", "D2"),
                      ("时点误判", "事件公告日与生效日不同，窗口错位", "D1"),
                      ("假异常", "一字板导致量价失真，被读成放量", "D2"),
                      ("材料冲突", "龙虎榜与逐笔资金流方向相反", "D3"),
                      ("状态误判", "停牌复牌前后换手率不可比", "D4")],
        params=["窗口长度与前后置期", "异常阈值定义", "自由流通股本来源", "事件剔除规则"],
        errors=["用总股本算换手", "窗口按公告日而非生效日", "把大宗交易计入竞价资金"],
    ),
    dict(
        code="FIN03", slug="ETF_ARB", auto="03 ETF 折溢价与套利",
        l2="基金与ETF研究评价", l3="分析ETF折溢价与申赎套利机制",
        platform="7705055652846309139", prio="优先试产",
        use="判断折溢价是否可套利，决定做市报价与套利下单",
        cost="忽略成本与申赎限制，会把不可套利的价差当成机会",
        inputs=[("ETF_QUOTES", "fund+trade_date+ts", ["fund_code", "trade_date", "ts", "bid", "ask", "last", "volume"]),
                ("NAV_IOPV", "fund+trade_date+ts", ["fund_code", "trade_date", "ts", "nav", "iopv", "nav_date"]),
                ("PCF_BASKET", "fund+trade_date", ["fund_code", "trade_date", "component", "qty", "cash_substitute", "premium_ratio"]),
                ("FEES", "fund", ["fund_code", "fee_type", "rate", "min_amount", "note"])],
        outputs=["D1 PREMIUM_DISCOUNT（逐日逐时点折溢价，含 IOPV 口径说明）", "D2 ARB_ECONOMICS（逐笔套利成本与净空间）",
                 "D3 可套利/不可套利判定与理由", "D4 口径与缺口登记"],
        chain=["IOPV 口径", "篮子与现金替代", "折溢价计算", "套利成本", "可执行性判断"],
        difficulties=[("口径不一致", "IOPV 与实际净值（T 日收盘 vs T-1 净值）混用", "D1"),
                      ("多约束", "T+0/T+1 申赎限制、成分股停牌、现金替代溢价", "D2"),
                      ("边界取值", "折溢价恰等于总成本线，判可套利还是不可", "D3"),
                      ("顺手方法失效", "按最新价算折溢价，忽略买卖价差与冲击", "D2"),
                      ("材料冲突", "PCF 成分数量与基金公告不一致（分红/拆分）", "D4")],
        params=["折溢价基准（IOPV/净值）", "总成本构成", "最小申赎单位", "停牌成分处理"],
        errors=["用 T-1 净值算 T 日折溢价", "漏掉现金替代溢价", "忽略买卖价差"],
    ),
    dict(
        code="FIN04", slug="PORT_ATTR", auto="04 组合收益归因",
        l2="持仓诊断与投资决策辅助", l3="归因个人组合收益与基准偏离",
        platform="7705055555161820947", prio="候选",
        use="向客户解释赚在哪、亏在哪，决定是否调仓",
        cost="归因错会把 beta 说成 alpha，误导客户与合规",
        inputs=[("POSITIONS", "account+symbol+date", ["account", "symbol", "date", "qty", "price", "market_value", "currency"]),
                ("TRANSACTIONS", "txn_id", ["txn_id", "account", "symbol", "trade_date", "side", "qty", "price", "fee", "fx_rate"]),
                ("BENCHMARK", "benchmark+date", ["benchmark", "date", "return", "weight_scheme"])],
        outputs=["D1 RETURN_RECON（时间加权/资金加权对平）", "D2 ATTRIBUTION（配置/选股/交互，或行业/个股）",
                 "D3 基准偏离解释与残差", "D4 口径与缺口登记"],
        chain=["收益口径", "现金流处理", "权重方案", "归因分解", "偏离解释"],
        difficulties=[("口径不一致", "TWR 与 MWR 在有大额申赎时差异巨大", "D1"),
                      ("状态误判", "分红送转导致持仓与价格不可直接连乘", "D2"),
                      ("多约束", "多币种组合的汇率贡献须单列", "D3"),
                      ("顺手方法失效", "用期初期末权重做归因（应逐日链接）", "D2"),
                      ("假异常", "基准缺失被当作 0 收益", "D4")],
        params=["收益口径（TWR/MWR）", "权重方案", "费用与税的处理", "汇率折算时点"],
        errors=["忽略申赎现金流", "用简单相减算超额", "分红未复权"],
    ),
    dict(
        code="FIN05", slug="FX_SHOCK", auto="05 汇率冲击",
        l2="宏观与市场策略研究", l3="评估汇率冲击影响",
        platform="7705055005066317587", prio="候选",
        use="判断汇率波动对组合与现金流的影响，决定是否加对冲",
        cost="暴露识别漏项会导致对冲不足或过度对冲",
        inputs=[("FX_EXPOSURE", "entity+currency", ["entity", "currency", "exposure_amount", "exposure_type", "as_of"]),
                ("CASHFLOWS", "flow_id", ["flow_id", "entity", "currency", "due_date", "amount", "direction"]),
                ("HEDGES", "hedge_id", ["hedge_id", "currency", "notional", "strike", "maturity", "instrument"])],
        outputs=["D1 SCENARIO_IMPACT（多情景汇率冲击与损益）", "D2 HEDGE_GAP（逐币种对冲缺口）",
                 "D3 敏感性与结论", "D4 口径与缺口登记"],
        chain=["敞口识别", "现金流时点", "情景设定", "重估", "对冲缺口"],
        difficulties=[("口径不一致", "会计敞口 vs 经济敞口", "D1"),
                      ("状态误判", "已签未交割远期未计入敞口", "D2"),
                      ("多约束", "对冲比例上限与授信额度共同约束", "D3"),
                      ("边界取值", "冲击幅度恰在容忍线", "D3"),
                      ("假异常", "与本币无关的收入被计入外敞口", "D4")],
        params=["情景幅度与方向", "折算汇率来源", "对冲工具口径", "敞口时间边界"],
        errors=["只算资产不算负债", "用期末汇率折全部现金流", "漏掉交叉货币对"],
    ),
    dict(
        code="FIN06", slug="CREDIT_MIGRATION", auto="06 信用评级迁移",
        l2="信用与固定收益研究", l3="识别信用评级迁移风险",
        platform="7705055524749086518", prio="候选",
        use="识别发行人下迁风险，决定持仓限额与预警",
        cost="迁移矩阵算错会低估违约概率，导致超限持有",
        inputs=[("ISSUER", "issuer_id", ["issuer_id", "name", "industry", "region", "external_rating", "outlook"]),
                ("RATING_HISTORY", "issuer_id+date", ["issuer_id", "date", "rating", "agency", "action"]),
                ("FINANCIALS", "issuer_id+period", ["issuer_id", "period", "revenue", "ebitda", "debt", "interest", "cash"])],
        outputs=["D1 MIGRATION_MATRIX（迁移矩阵与样本口径）", "D2 ISSUER_WATCHLIST（预警名单与触发条件）",
                 "D3 敞口与限额对照", "D4 口径与缺口登记"],
        chain=["评级序列清洗", "迁移统计", "矩阵估计", "发行人打分", "预警与限额"],
        difficulties=[("口径不一致", "跨机构评级不可直接拼接（符号体系不同）", "D1"),
                      ("状态误判", "评级展望调整不等于评级迁移", "D1"),
                      ("素材不足", "小样本下迁移概率为 0 不等于无风险（需平滑）", "D2"),
                      ("多约束", "限额同时受评级与集中度约束", "D3"),
                      ("假异常", "未评级发行人被当作最高等级", "D4")],
        params=["评级符号映射", "样本期与平滑方法", "违约定义", "限额规则"],
        errors=["把展望下调计为迁移", "小样本直接取 0", "未评级当 AAA"],
    ),
    dict(
        code="FIN07", slug="STRESS", auto="07 压力情景设计",
        l2="压力测试与风险限额", l3="设计压力情景",
        platform="7705054469567057727", prio="候选",
        use="为限额管理设定情景与触发线，决定是否降杠杆",
        cost="情景相关性假设错会让压力损失被系统性低估",
        inputs=[("EXPOSURES", "portfolio+factor", ["portfolio", "factor", "exposure", "as_of"]),
                ("RISK_FACTOR_HISTORY", "factor+date", ["factor", "date", "value"]),
                ("LIMITS", "limit_id", ["limit_id", "scope", "metric", "threshold", "breach_action"])],
        outputs=["D1 STRESS_RESULTS（逐情景逐因子重估）", "D2 LIMIT_BREACH（超限判定与处置）",
                 "D3 情景假设与相关性说明", "D4 口径与缺口登记"],
        chain=["因子映射", "情景设定", "联合冲击", "重估", "限额判定"],
        difficulties=[("多约束", "联合冲击需保持相关性结构，不能单因子相加", "D1"),
                      ("口径不一致", "线性暴露 vs 非线性（期权）暴露", "D2"),
                      ("边界取值", "损失恰等于限额", "D2"),
                      ("顺手方法失效", "用历史最大跌幅当情景，忽略同时性", "D1"),
                      ("假异常", "缺失因子被设为零冲击", "D4")],
        params=["情景来源与幅度", "因子相关性矩阵", "非线性处理", "限额口径"],
        errors=["单因子冲击相加", "缺失因子当 0", "忽略期权凸性"],
    ),
    dict(
        code="FIN08", slug="LIQUIDITY_GAP", auto="08 流动性缺口",
        l2="投资风险管理", l3="评估流动性缺口",
        platform="7705055005065203475", prio="候选",
        use="判断到期兑付能否覆盖，决定备付与资产变现安排",
        cost="缺口低估会导致被动折价变现甚至违约",
        inputs=[("CASHFLOWS", "flow_id", ["flow_id", "bucket", "direction", "amount", "currency", "certainty"]),
                ("LIQUID_ASSETS", "asset_id", ["asset_id", "asset_class", "market_value", "haircut", "settle_days", "is_pledged"]),
                ("LIABILITIES", "liability_id", ["liability_id", "due_date", "amount", "callable", "priority"])],
        outputs=["D1 GAP_LADDER（期限阶梯缺口）", "D2 COVERAGE（覆盖率与压力情景）",
                 "D3 变现假设与折扣依据", "D4 口径与缺口登记"],
        chain=["现金流分桶", "变现折扣", "质押冻结剔除", "缺口计算", "覆盖率结论"],
        difficulties=[("口径不一致", "合同到期日 vs 实际可赎回日", "D1"),
                      ("状态误判", "已质押资产仍计入可变现", "D2"),
                      ("多约束", "变现受结算天数与折价率共同约束", "D2"),
                      ("边界取值", "覆盖率恰等于 100%", "D2"),
                      ("假异常", "NOT_PROVEN 的应收被当作可回收", "D4")],
        params=["分桶粒度", "折价率来源", "可变现定义", "覆盖率阈值"],
        errors=["质押资产计入流动性", "忽略结算天数", "应收全按可回收"],
    ),
]

PLATFORM_RUBRIC_HEADER = ["item_no", "类型", "核心判分点", "达标标准", "专业判断说明",
                          "依据来源与位置", "数值与容差", "合理替代", "Gate候选"]
INTERNAL_HEADER = ["criterion_id", "维度", "观测点", "machine_checkable", "weight"]
RUNLOG_HEADER = ["run_id", "task_id", "prompt_sha256", "model", "mode", "judge_score",
                 "model_steps", "duration_seconds", "status", "notes"]
SOURCE_HEADER = ["source_id", "type", "url_or_ref", "publisher", "released_at", "license",
                 "authorized", "desensitized", "sha256", "note"]
ACCEPT_HEADER = ["file", "expected_rows", "actual_rows", "required_fields_ok", "verdict", "note"]
C20_HEADER = ["review_id", "reviewer", "independent_of_author", "score_0_5", "verdict", "evidence", "date"]
EVIDENCE_HEADER = ["run_id", "prompt_sha256", "attachment_hashes", "output_files", "tool_calls",
                   "started_at", "ended_at", "human_intervention", "verdict"]


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def csv_text(header: list[str], rows: list[list[str]] | None = None) -> str:
    buf = io.StringIO()
    wr = csv.writer(buf, lineterminator="\n")
    wr.writerow(header)
    for r in rows or []:
        wr.writerow(r)
    return buf.getvalue()


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def build_task(t: dict) -> Path:
    d = OUT / f"{t['code']}_{t['slug']}"
    name = f"{t['code']}_{t['slug']}"
    l2, l3 = t["l2"], t["l3"]

    w(d / "CASE_CARD.md", f"""# CASE_CARD · {t['auto']}

| 项 | 值 |
|---|---|
| 本地编号 | `{t['code']}` |
| 三级 Skill | **{l3}** |
| 二级 Skill | {l2} |
| 平台 Task ID | `{t['platform']}` |
| 优先级 | {t['prio']} |
| 行业 | 金融 |
| 当前状态 | **SCAFFOLD**（脚手架，非可提交题目） |

## 业务用途

{t['use']}

## 判错的代价

{t['cost']}

## 资质提示

{l3} 需要对应岗位的真实工作案例与专家资质；本包只提供生产脚手架，
**取得真实授权材料前不得提交**。

## 决策链

{chr(10).join(f'{i}. {c}' for i, c in enumerate(t['chain'], 1))}

## 必填业务参数（须有材料依据，禁止填行业默认值）

{chr(10).join(f'- {p}' for p in t['params'])}
""")

    w(d / "OUTPUT_CONTRACT.md", f"""# OUTPUT_CONTRACT · {l3}

交付物必须可编辑、可逐条判定、可回溯到材料 ID。

## 交付物

{chr(10).join(t['outputs'])}

## 硬性要求

1. 每个结论必须写到材料中的记录 ID，不得只写文件名。
2. 计算类结论须给出公式与两侧实际值，不得只给最终数。
3. 计数须给出「分部之和＝总数」勾稽。
4. 材料未提供的信息登记为 `NOT_PROVEN`，不得补零、不得自拟阈值。
5. 事实、假设、待核三类必须分开列示。
6. 存在多种合理口径时，须并列两种口径结果并声明采纳哪一种。
7. 口径缺口与弃权事项单列，写明涉及对象、缺什么、取值、影响。
8. 输出文件禁用宏、外部链接、隐藏答案表。
""")

    w(d / "01_PUBLIC_DOUBAO/PROMPT.template.md", f"""# 题面模板 · {l3}

> 占位符在取得真实材料与冻结考点后填写。**题面不得出现结论、阈值、考点用语。**

【角色与场景】
你是{{{{ROLE}}}}。当前需要完成{{{{TASK_OBJECT}}}}，结果将用于{{{{DECISION_USE}}}}。
证据截止时点：{{{{AS_OF}}}}。

【可用材料】
{{{{MATERIALS_LIST}}}}

【判定口径】
口径只写在材料内的制度/标准文件中；题面不复述阈值，不提示边界值。

【任务：交付物】
{{{{DELIVERABLES}}}}

【交付要求（硬性）】
{{{{REQUIREMENTS}}}}

【边界】
仅可依据材料作答；未提供的信息登记为待核；不得使用外部检索结果替代材料。
""")

    w(d / "01_PUBLIC_DOUBAO/INPUT_CONTRACT.md", f"""# INPUT_CONTRACT · {l3}

材料落 `inputs/`，命名 `{{{{序号}}}}_{{{{对象}}}}.{{{{ext}}}}`。逐件给出行数、主键、字段与单位。

| 文件 | 业务主键 | 必备字段 |
|---|---|---|
""" + "\n".join(f"| `{n}.csv` | `{k}` | {', '.join(f'`{x}`' for x in cols)} |"
                for n, k, cols in t["inputs"]) + """

## 通用约束

- 编码 UTF-8（含 BOM 亦可）；日期 ISO-8601 且注明时区；金额注明币种与精度。
- 空值必须区分 `UNKNOWN` / `NOT_OBSERVED` / `NOT_PROVEN` / `NOT_RUN`。
- 每份文件计算 SHA-256，写入 `04_EVIDENCE/SOURCE_REGISTER.csv`。
- **缺少任一必备字段即材料不合格**，先补材料，不讨论难度。
""")

    w(d / "02_PRIVATE_EXPERT/CASE_INTAKE.md", f"""# CASE_INTAKE · {l3}

> 真实性门禁 A1–A7（与产线 `case_intake/authenticity_gate.py` 同规则）。任一不过即拒绝进入生成。

- [ ] A1 来源可定位（URL / 合同编号 / 台账编号）
- [ ] A2 source_type 合法（real / public / synthetic）
- [ ] A3 real 必须有授权与脱敏标记
- [ ] A4 public 必须有发布日
- [ ] A5 synthetic 必须在题面标注合成
- [ ] A6 材料内无高危 PII（身份证/银行卡/手机号）
- [ ] A7 三级 Skill `{l3}` 未被占用

## 授权与脱敏记录

| 项 | 内容 |
|---|---|
| 材料提供方 | TODO |
| 授权方式 | TODO |
| 脱敏处理 | TODO |
| 业务时点 | TODO |
""")

    w(d / "02_PRIVATE_EXPERT/IDEAL_STEPS.template.md", f"""# IDEAL_STEPS · {l3}

按决策链展开，每步写清：读什么、做什么、判什么、异常怎么办。

{chr(10).join(f'## 步骤 {{i}} · {c}' + chr(10) + '- 读：TODO' + chr(10) + '- 做：TODO' + chr(10) + '- 判：TODO' + chr(10) + '- 异常：TODO' for c in t['chain'])}

> 步骤数不用于凑难度；难度来自前置判断向下游的传播。
""")

    w(d / "02_PRIVATE_EXPERT/GOLDEN_RESPONSE.template.md", f"""# GOLDEN_RESPONSE · {l3}

**本文件当前为空模板，这是有意为之。**

标准答案必须由独立计算或独立复核产生，且能逐条对应冻结考点。禁止：
- 用 AI 生成"看起来专业"的数值；
- 用模型自述当答案；
- 先写答案再倒推考点。

## 三层 GT

| 层 | 内容 | 来源要求 |
|---|---|---|
| Narrative GT | 专业意见与结论 | 由计算结论拼装，不自由发挥 |
| Calculation GT | 数值与公式 | 必须由确定性计算器产出（Decimal） |
| Evidence GT | 文件＋字段＋记录号 | 每条数值挂锚点 |

## 产出后自检

- [ ] 三层互相一致
- [ ] 每个数值可被材料复算
- [ ] 与冻结考点逐条对齐
""")

    rows = [["R1", "必需项", "TODO", "TODO", "TODO", "TODO", "TODO", "TODO", ""]]
    w(d / "02_PRIVATE_EXPERT/PLATFORM_EXPERT_RUBRIC.template.csv", csv_text(PLATFORM_RUBRIC_HEADER, rows))

    rows = [[f"C{i:02d}", "TODO", "TODO", "TRUE", "1"] for i in range(1, 20)]
    rows.append(["C20", "专家人工独立评审", "TODO", "FALSE", "5"])
    w(d / "02_PRIVATE_EXPERT/INTERNAL_GRADER_20x5.template.csv", csv_text(INTERNAL_HEADER, rows))

    rows = [[f"H{i}", typ, text, gate, l3] for i, (typ, text, gate) in enumerate(t["difficulties"], 1)]
    w(d / "02_PRIVATE_EXPERT/HIDDEN_DIFFICULTY_MAP.template.csv",
      csv_text(["hidden_id", "机制", "隐藏难点", "对应交付物", "对应三级 Skill"], rows))

    w(d / "02_PRIVATE_EXPERT/RUBRIC_RULES.md", f"""# RUBRIC_RULES · {l3}

## 两套 Rubric 不混用

| 文件 | 用途 | 计分 |
|---|---|---|
| `PLATFORM_EXPERT_RUBRIC.template.csv` | Xpert 平台专家 Rubric（11.4 字段） | 平台百分制 |
| `INTERNAL_GRADER_20x5.template.csv` | 内部评测（C01–C19 ＋ C20 人工） | 95 ＋ 5 |
| `HIDDEN_DIFFICULTY_MAP.template.csv` | 隐藏难点 → 考点的映射 | 不入分 |
| `04_EVIDENCE/C20_REVIEW.csv` | 专家人工独立评审留痕 | 5 |

**内部 20×5 不能替代平台 Rubric**，两者分别维护、分别冻结。

## 11.4 平台 Rubric 要求

- 必需项＋负向项合计 5–12 条；复杂任务可到 15 条以上，但须给复杂度依据。
- 加分项最多 2 条，不计入上述条数，**不得作为 Gate**。
- Gate 候选最多 3 条。
- 每条必须写：类型、核心判分点、达标标准、专业判断说明、依据来源与位置、
  数值与容差、合理替代。
- 一条只查一件事；禁止"考虑了 XX"这类灰度表述。
- 数值型必须给精度与容差；开放项必须给可接受替代。

## 生成方式

正式 Rubric 由 `generators/rubric_builder.py` 从题面交付要求独立抽取
（不读 GT），再用 `evaluation/rubric_qa.py` 六检查器过一遍。
""")

    w(d / "03_OPERATIONS/CASE_MANIFEST.json", json.dumps({
        "task_code": t["code"], "task_slug": t["slug"], "local_name": name,
        "industry_l1": "金融", "l2_skill": l2, "level3_skill": l3,
        "platform_task_id": t["platform"], "priority": t["prio"],
        "source_type": "TBD", "status": "SCAFFOLD",
        "inputs": [{"file": f"{n}.csv", "primary_key": k, "fields": c} for n, k, c in t["inputs"]],
        "deliverables": t["outputs"],
        "decision_chain": t["chain"],
        "policy_parameters": t["params"],
        "typical_errors": t["errors"],
        "difficulty_gate": {"rule_id": "XPERT-DIFF-11.4", "judge_max": 50,
                            "steps_min": 50, "duration": "rating_only"},
        "created_at": "2026-11-09T18:24:06+08:00",
    }, ensure_ascii=False, indent=2) + "\n")

    w(d / "03_OPERATIONS/RUN_LOG.csv", csv_text(RUNLOG_HEADER))

    w(d / "04_EVIDENCE/SOURCE_REGISTER.csv", csv_text(SOURCE_HEADER))
    w(d / "04_EVIDENCE/MATERIAL_ACCEPTANCE.csv",
      csv_text(ACCEPT_HEADER, [[f"{n}.csv", "", "", "", "PENDING", "待真实材料"] for n, _, _ in t["inputs"]]))
    w(d / "04_EVIDENCE/C20_REVIEW.csv", csv_text(C20_HEADER))
    w(d / "04_EVIDENCE/MODEL_RUN_EVIDENCE.csv", csv_text(EVIDENCE_HEADER))
    w(d / "04_EVIDENCE/HASHING.md", """# HASHING

- 每个文件计算 SHA-256，写入同目录 `MANIFEST.sha256`（格式：`hash  relative/path`）。
- 校验：`cd <包目录> && shasum -a 256 -c MANIFEST.sha256`
- `MANIFEST.sha256` 自身不入清单（避免自引用）。
- 材料被替换即整包失效，必须重算并留痕。
""")

    w(d / "05_PLATFORM_FIELDS/PLATFORM_FIELDS.md", f"""# PLATFORM_FIELDS · {l3}

| 字段 | 内容 | 状态 |
|---|---|---|
| 任务名称 | {t['auto']}（对象＋版本＋动作） | 待定稿 |
| 任务类型 | TODO（按交付物形态填） | 待定稿 |
| L1/L2 行业 | 金融 / TODO | 待定稿 |
| L1/L2 职业 | TODO | 待定稿 |
| 三级 Skill | **{l3}** | 平台 Task ID `{t['platform']}` |
| 题目-文字 | 见 `01_PUBLIC_DOUBAO/PROMPT.template.md` | 待填占位符 |
| 题目-附件 | 见 `INPUT_CONTRACT.md` | 待真实材料 |
| 考点 | 见 `PLATFORM_EXPERT_RUBRIC.template.csv` | 待冻结 |
| 作答思路 | 见 `IDEAL_STEPS.template.md` | 待填 |
| 标准答案 | 见 `GOLDEN_RESPONSE.template.md` | **待独立计算** |
""")

    w(d / "06_READINESS/READINESS_GATES.md", f"""# READINESS_GATES · {l3}

| 闸 | 条件 | 当前状态 | 阻塞项 |
|---|---|---|---|
| G0 | 版本与代码冻结 | ⬜ | 未冻结 |
| G1 | 真实来源、授权、许可 | ⬜ | 无真实材料 |
| G2 | Prompt 与输入输出契约 | 🟡 | 模板已建，占位符未填 |
| G3 | 8–15 个真实隐藏难点 | 🟡 | 已列 {len(t['difficulties'])} 项，待与材料核对 |
| G4 | Reference / Alternative / Negative | ⬜ | 无 GT |
| G5 | Schema Preflight ＋ Evidence Grader | ⬜ | 未接入 |
| G6 | 豆包盲测及完整运行记录 | ⬜ | 未运行（UNTESTED） |
| G7 | Judge ≤50 且 单轮步数 ≥50 | ⬜ | 无运行数据；**时长仅评级** |
| G8 | C20 人工专家校准 | ⬜ | 未评审 |
| G9 | 平台字段与提交就绪 | ⬜ | 见 PLATFORM_FIELDS |
| G10 | 独立归档及总包验证 | 🟡 | 归档已生成，待真实材料后重打包 |

> 全部 ⬜ 通过前，本包状态只能是 **SCAFFOLD**，不得提交。
""")

    w(d / "README_STATUS.md", f"""# README_STATUS · {name}

| 项 | 值 |
|---|---|
| 题目 | {t['auto']} |
| 三级 Skill | {l3} |
| 平台 Task ID | `{t['platform']}` |
| 文件数 | 23（不含 `inputs/` 内材料） |
| 状态 | **SCAFFOLD — 不可提交** |

## 这个包有什么

结构、契约、门禁、难点清单、两套 Rubric 的空白框架。
拿到真实授权材料后，按 `06_READINESS/READINESS_GATES.md` 的 G1→G10 顺序推进。

## 这个包没有什么（故意的）

- 没有业务数据：`01_PUBLIC_DOUBAO/inputs/` 为空。
- 没有标准答案：`GOLDEN_RESPONSE.template.md` 是空模板。
- 没有跑过豆包：`RUN_LOG.csv` 只有表头。

不生成这些，是因为它们必须来自真实材料与真实运行；用 AI 编出来的数值会让整道题作废。
""")

    (d / "01_PUBLIC_DOUBAO/inputs").mkdir(parents=True, exist_ok=True)
    w(d / "01_PUBLIC_DOUBAO/inputs/.gitkeep", "")

    # 逐文件哈希
    lines = []
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.sha256":
            lines.append(f"{sha256(p)}  {p.relative_to(d)}")
    w(d / "MANIFEST.sha256", "\n".join(lines) + "\n")

    # 交付清单
    files = sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file())
    w(d / "DELIVERY_MANIFEST.json", json.dumps({
        "task_code": t["code"], "level3_skill": l3, "platform_task_id": t["platform"],
        "file_count": len(files), "files": files,
        "status": "SCAFFOLD",
        "note": "含 inputs/.gitkeep；真实材料接入后须重算 MANIFEST.sha256",
    }, ensure_ascii=False, indent=2) + "\n")

    # 哈希因 DELIVERY_MANIFEST 新增而需重算
    lines = []
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.sha256":
            lines.append(f"{sha256(p)}  {p.relative_to(d)}")
    w(d / "MANIFEST.sha256", "\n".join(lines) + "\n")
    return d


def build_master(dirs: list[Path]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    registry = {
        "batch": "FIN8-20261109", "industry": "金融",
        "standard": "FDE 11.4", "difficulty_gate": {
            "rule": "judge<=50 AND model_steps>=50", "duration": "rating_only"},
        "tasks": [{"code": t["code"], "level3_skill": t["l3"], "platform_task_id": t["platform"],
                   "priority": t["prio"], "package": f"{t['code']}_{t['slug']}.zip",
                   "status": "SCAFFOLD"} for t in TASKS],
        "counts": {"tasks": len(TASKS), "files_per_task": 23,
                   "base_price_cny": 1500,
                   "theoretical_total_cny": 1500 * len(TASKS),
                   "note": "理论结算额＝8×1500，按全部质检合格计；不是收入保证"},
    }
    w(OUT / "BATCH_REGISTRY.json", json.dumps(registry, ensure_ascii=False, indent=2) + "\n")

    zips = []
    for d in dirs:
        z = OUT / f"{d.name}.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(d.rglob("*")):
                if p.is_file():
                    zf.write(p, str(Path(d.name) / p.relative_to(d)))
        with zipfile.ZipFile(z) as zf:
            bad = zf.testzip()
            if bad:
                raise RuntimeError(f"CRC 校验失败：{z.name}:{bad}")
        zips.append(z)

    master = OUT / "FINANCIAL_8_TASKS_MASTER_SCAFFOLD.zip"
    with zipfile.ZipFile(master, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT / "BATCH_REGISTRY.json", "BATCH_REGISTRY.json")
        for z in zips:
            zf.write(z, f"packages/{z.name}")
        zf.writestr("MASTER_README.md", "\n".join([
            "# 金融八题 · 总包（SCAFFOLD）", "",
            f"- 题目数：{len(TASKS)}；每包 23 个文件",
            "- 全部为脚手架：无业务数据、无标准答案、未跑豆测",
            "- 难度闸门：Judge ≤50 且 单轮步数 ≥50（时长只评级）",
            "- 理论结算：8 × 1,500 = 12,000 元（按全部质检合格计，非收入保证）", "",
            "## 包清单", "",
        ] + [f"- `packages/{z.name}`" for z in zips]))
        for p in sorted(OUT.glob("*.zip")):
            if p.name in {z.name for z in zips}:
                pass
    with zipfile.ZipFile(master) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"总包 CRC 失败：{bad}")
    return master


def verify() -> int:
    fails = []
    dirs = sorted(p for p in OUT.iterdir() if p.is_dir())
    if len(dirs) != 8:
        fails.append(f"包数 {len(dirs)} != 8")
    for d in dirs:
        files = [p for p in d.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256"]
        if len(files) != 23:
            fails.append(f"{d.name}: {len(files)} 文件 != 23")
        if any((d / "01_PUBLIC_DOUBAO/inputs").glob("*.csv")):
            fails.append(f"{d.name}: inputs 出现业务数据（脚手架不得含材料）")
        gt = (d / "02_PRIVATE_EXPERT/GOLDEN_RESPONSE.template.md").read_text(encoding="utf-8")
        if "TODO" not in gt and "空模板" not in gt:
            fails.append(f"{d.name}: GT 被填过，脚手架阶段不允许")
        log = (d / "03_OPERATIONS/RUN_LOG.csv").read_text(encoding="utf-8").strip().splitlines()
        if len(log) != 1:
            fails.append(f"{d.name}: RUN_LOG 出现运行记录")
        # 哈希清单
        import subprocess
        r = subprocess.run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=d,
                           capture_output=True, text=True)
        if r.returncode != 0:
            fails.append(f"{d.name}: MANIFEST 校验失败")
    master = OUT / "FINANCIAL_8_TASKS_MASTER_SCAFFOLD.zip"
    if not master.is_file():
        fails.append("缺总包")
    for f in fails:
        print("FAIL", f)
    print(f"{len(fails)} 失败 / 8 包校验")
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    dirs = [build_task(t) for t in TASKS]
    master = build_master(dirs)
    print(f"生成 {len(dirs)} 包 -> {OUT}")
    for d in dirs:
        n = len([p for p in d.rglob('*') if p.is_file() and p.name != 'MANIFEST.sha256'])
        print(f"  {d.name}: {n} 文件")
    print(f"总包 {master.name} {master.stat().st_size // 1024} KB")
    return verify() if a.verify else 0


if __name__ == "__main__":
    raise SystemExit(main())
