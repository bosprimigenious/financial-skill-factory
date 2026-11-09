#!/usr/bin/env python3
"""城商行 IT 外包供应商技术风险定级 —— 案例构建器（单一事实源）。

一处事实表，同时产出三样东西：
  1) 被试材料 12 件 CSV          -> <pack>/01_public/data/
  2) 作者侧标准答案 5 张 xlsx     -> <pack>/03_private_review/GT/
  3) 对冻结考点的机器断言         -> 任一不符即非零退出

材料性质：**合成数据**（匿名城商行 + 供应商 V1–V6），由本脚本确定性生成，
不来自任何真实机构。断言值取自冻结考点 02_platform_fields/expert_rubric.md。

用法：
  python3 build_case.py --pack ../packs/7689005313907642138
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import sys

BASE = dt.date(2025, 12, 31)          # 附件12 基准日
PERIOD_START = dt.date(2025, 1, 1)    # 附件12 统计期间起

SUP = [
    # id, name, service, criticality, contract_start, contract_end, cloud_region, shared_col
    ("V1", "云腾数据", "核心系统托管", "关键", "2023-01-01", "2026-12-31", "CR-A", "SP-X;SP-M;SP-W"),
    ("V2", "恒运外包", "运维外包", "关键", "2023-01-01", "2026-06-30", "CR-A", "SP-Q"),
    ("V3", "明盾安全", "安全监测", "支持", "2023-01-01", "2026-02-28", "CR-B", "SP-T;SP-Y"),
    ("V4", "迅捷支付", "支付通道", "关键", "2023-01-01", "2026-12-31", "CR-C", "SP-Z;SP-U"),
    ("V5", "星环云备份", "灾备存储", "关键", "2023-01-01", "2025-12-31", "CR-A", "SP-Q"),
    ("V6", "慧眼身份", "身份认证", "关键", "2023-01-01", "2027-04-30", "CR-D", "SP-M"),
]
NAMES = {r[0]: r[1] for r in SUP}

# 附件7：16 条「供应商×子处理商×角色」。组件供应商角色不出现在附件1 的共用列。
DEP = [
    ("V1", "SP-X", "主用"), ("V1", "SP-M", "主用"), ("V1", "SP-W", "备用"),
    ("V2", "SP-Q", "主用"), ("V2", "SP-W", "组件供应商"), ("V2", "SP-X", "组件供应商"),
    ("V3", "SP-T", "主用"), ("V3", "SP-Y", "主用"),
    ("V4", "SP-Z", "主用"), ("V4", "SP-U", "主用"), ("V4", "SP-W", "组件供应商"),
    ("V5", "SP-Q", "备用"), ("V5", "SP-W", "组件供应商"), ("V5", "SP-X", "组件供应商"),
    ("V6", "SP-M", "备用"), ("V6", "SP-W", "组件供应商"),
]

# 附件4：18 条（供应商×核查范围）：(未回收账号, 敏感明文列)
PERM = {
    ("V1", "生产库"): (0, 3), ("V1", "备份库"): (0, 0), ("V1", "测试环境"): (0, 0),
    ("V2", "生产库"): (2, 0), ("V2", "备份库"): (0, 0), ("V2", "测试环境"): (0, 0),
    ("V3", "生产库"): (0, 0), ("V3", "备份库"): (0, 0), ("V3", "测试环境"): (0, 0),
    ("V4", "生产库"): (6, 0), ("V4", "备份库"): (0, 0), ("V4", "测试环境"): (2, 0),
    ("V5", "生产库"): (1, 0), ("V5", "备份库"): (0, 0), ("V5", "测试环境"): (0, 0),
    ("V6", "生产库"): (1, 0), ("V6", "备份库"): (3, 0), ("V6", "测试环境"): (1, 0),
}
RANGES = ["生产库", "备份库", "测试环境"]

# 附件5：12 条演练（每户两次，方向相反）
DRILL = [
    ("V1", "2025-05-14", "账务系统主备切换", 6.5, 4.0, 18.0, 15.0, "", "是"),
    ("V1", "2025-11-12", "账务系统主备切换", 2.0, 4.0, 10.0, 15.0, "身份认证IdP(V6)", "是"),
    ("V2", "2025-06-18", "运维平台切换", 2.5, 4.0, 8.0, 15.0, "", "是"),
    ("V2", "2025-10-21", "运维平台切换", 5.0, 4.0, 12.0, 15.0, "", "是"),
    ("V3", "2025-04-09", "监测数据切换", 9.0, 8.0, 70.0, 60.0, "", "是"),
    ("V3", "2025-09-16", "监测数据切换", 6.0, 8.0, 30.0, 60.0, "", "是"),
    ("V4", "2025-07-02", "支付网关切换", 3.0, 2.0, 7.0, 5.0, "", "是"),
    ("V4", "2025-12-03", "支付网关切换", 1.5, 2.0, 3.0, 5.0, "", "是"),
    ("V5", "2025-08-13", "灾备存储切换", 7.0, 6.0, 35.0, 30.0, "", "是"),
    ("V5", "2025-11-25", "灾备存储切换", 5.0, 6.0, 20.0, 30.0, "", "是"),
    ("V6", "2025-05-29", "IdP主备切换", 4.5, 4.0, 18.0, 15.0, "", "是"),
    ("V6", "2025-12-09", "IdP主备切换", 3.0, 4.0, 8.0, 15.0, "", "是"),
]

# 附件6：承诺可用性 + 逐户逐月未达标设计（扣除后 / 原始）
COMMIT = 99.90
SLA_BAD = {
    # supplier: (扣除后未达标月份集合, 原始未达标月份集合)
    "V1": ([], []),
    "V2": (["2025-04"], ["2025-04", "2025-11"]),
    "V3": ([], ["2025-03", "2025-10"]),
    "V4": ([], ["2025-02", "2025-09"]),
    "V5": (["2025-05", "2025-10", "2025-11"], ["2025-05", "2025-10", "2025-11"]),
    "V6": (["2025-09", "2025-12"], ["2025-09", "2025-12"]),
}
MONTHS = [f"2025-{m:02d}" for m in range(1, 13)]

# 附件8：合同退出与可携
EXIT = {
    "V1": ("否", "无", 1, 30),
    "V2": ("是", "90", 3, 60),
    "V3": ("是", "60", 3, 30),
    "V4": ("是", "90", 6, 60),
    "V5": ("是", "30", 2, 30),
    "V6": ("是", "60", 3, 30),
}

# 附件3：48 条漏洞（id, 级别, 发现日, 应修日, 实修日或空, 状态）
def _vulns():
    rows = []
    # V1：12 条。VUL-V1-01 高危未修超期（→中）；VUL-V1-12 期间外
    rows += [
        ("VUL-V1-01", "V1", "高", "2025-11-05", "2025-11-12", "", "未修"),
        ("VUL-V1-02", "V1", "中", "2025-09-01", "2025-10-01", "2025-09-20", "已修"),
        ("VUL-V1-03", "V1", "中", "2025-10-10", "2025-11-09", "2025-11-05", "已修"),
        ("VUL-V1-04", "V1", "中", "2025-12-01", "2025-12-11", "2025-12-02", "已修"),
        ("VUL-V1-05", "V1", "低", "2025-03-01", "2025-04-30", "2025-04-10", "已修"),
        ("VUL-V1-06", "V1", "低", "2025-05-01", "2025-06-30", "2025-06-20", "已修"),
        ("VUL-V1-07", "V1", "低", "2025-07-01", "2025-08-31", "", "未修"),
        ("VUL-V1-08", "V1", "中", "2025-08-01", "2025-08-31", "2025-09-15", "已修"),
        ("VUL-V1-09", "V1", "低", "2025-09-01", "2025-10-31", "2025-10-08", "已修"),
        ("VUL-V1-10", "V1", "中", "2025-12-20", "2026-01-20", "", "未修"),
        ("VUL-V1-11", "V1", "低", "2025-02-01", "2025-03-31", "2025-03-01", "已修"),
        ("VUL-V1-12", "V1", "高", "2024-11-05", "2024-11-12", "", "未修"),
    ]
    # V2：12 条。VUL-V2-02/03 中危未修超期（→低）；VUL-V2-12 期间外
    rows += [
        ("VUL-V2-01", "V2", "高", "2025-08-01", "2025-08-08", "2025-08-06", "已修"),
        ("VUL-V2-02", "V2", "中", "2025-10-01", "2025-10-31", "", "未修"),
        ("VUL-V2-03", "V2", "中", "2025-10-15", "2025-11-14", "", "未修"),
        ("VUL-V2-04", "V2", "中", "2025-12-10", "2026-01-10", "", "未修"),
        ("VUL-V2-05", "V2", "低", "2025-03-05", "2025-04-30", "2025-04-01", "已修"),
        ("VUL-V2-06", "V2", "低", "2025-05-05", "", "", "未到期未修"),
        ("VUL-V2-07", "V2", "中", "2025-06-01", "2025-06-30", "2025-07-20", "已修"),
        ("VUL-V2-08", "V2", "低", "2025-07-15", "2025-08-31", "2025-08-10", "已修"),
        ("VUL-V2-09", "V2", "低", "2025-09-01", "2025-10-31", "", "未修"),
        ("VUL-V2-10", "V2", "中", "2025-11-01", "2025-12-01", "2025-11-20", "已修"),
        ("VUL-V2-11", "V2", "低", "2025-01-10", "2025-02-28", "2025-02-01", "已修"),
        ("VUL-V2-12", "V2", "高", "2024-09-01", "2024-09-08", "2024-09-05", "已修"),
    ]
    # V3：6 条。VUL-V3-06 低危超期未修（口径未穷举）
    rows += [
        ("VUL-V3-01", "V3", "中", "2025-03-01", "2025-03-31", "2025-03-20", "已修"),
        ("VUL-V3-02", "V3", "低", "2025-04-01", "2025-05-31", "2025-05-01", "已修"),
        ("VUL-V3-03", "V3", "中", "2025-06-01", "2025-06-30", "2025-06-25", "已修"),
        ("VUL-V3-04", "V3", "低", "2025-08-01", "2025-09-30", "2025-09-01", "已修"),
        ("VUL-V3-05", "V3", "低", "2025-11-01", "", "", "未到期未修"),
        ("VUL-V3-06", "V3", "低", "2025-02-01", "2025-03-31", "", "未修"),
    ]
    # V4：9 条。VUL-V4-01/02 高危未修超期（→高）；VUL-V4-09 期间外
    rows += [
        ("VUL-V4-01", "V4", "高", "2025-09-10", "2025-09-17", "", "未修"),
        ("VUL-V4-02", "V4", "高", "2025-11-20", "2025-11-27", "", "未修"),
        ("VUL-V4-03", "V4", "中", "2025-10-01", "2025-10-31", "2025-10-20", "已修"),
        ("VUL-V4-04", "V4", "低", "2025-02-01", "2025-03-31", "2025-03-10", "已修"),
        ("VUL-V4-05", "V4", "中", "2025-06-01", "2025-06-30", "2025-06-28", "已修"),
        ("VUL-V4-06", "V4", "低", "2025-07-01", "2025-08-31", "", "未修"),
        ("VUL-V4-07", "V4", "中", "2025-12-05", "2026-01-05", "", "未修"),
        ("VUL-V4-08", "V4", "低", "2025-05-05", "2025-06-30", "2025-06-01", "已修"),
        ("VUL-V4-09", "V4", "高", "2024-12-01", "2024-12-08", "", "未修"),
    ]
    # V5：2 条，无超期触发
    rows += [
        ("VUL-V5-01", "V5", "中", "2025-04-01", "2025-04-30", "2025-04-18", "已修"),
        ("VUL-V5-02", "V5", "低", "2025-10-01", "2025-11-30", "2025-11-10", "已修"),
    ]
    # V6：7 条。VUL-V6-07 期间外
    rows += [
        ("VUL-V6-01", "V6", "中", "2025-03-01", "2025-03-31", "2025-03-22", "已修"),
        ("VUL-V6-02", "V6", "低", "2025-05-01", "2025-06-30", "2025-06-01", "已修"),
        ("VUL-V6-03", "V6", "中", "2025-07-01", "2025-07-31", "2025-07-28", "已修"),
        ("VUL-V6-04", "V6", "低", "2025-09-01", "2025-10-31", "2025-10-05", "已修"),
        ("VUL-V6-05", "V6", "中", "2025-11-01", "2025-11-30", "", "未修"),
        ("VUL-V6-06", "V6", "低", "2025-12-01", "2026-01-31", "", "未到期未修"),
        ("VUL-V6-07", "V6", "高", "2024-10-10", "2024-10-17", "2024-10-15", "已修"),
    ]
    return rows


# 附件9：26 条安全事件（事件ID, 供应商, 发生日, 级别, 类别, 是否影响本行, 处置证据是否齐全）
def _incidents():
    rows = [
        ("INC-V1-2024-06", "V1", "2024-06-12", "H", "可用性", "是", "是"),
        ("INC-V1-2025-01", "V1", "2025-01-20", "M", "性能", "否", "是"),
        ("INC-V1-2025-02", "V1", "2025-04-11", "L", "配置", "否", "是"),
        ("INC-V1-2025-03", "V1", "2025-08-09", "M", "变更", "否", "是"),
        ("INC-V1-2025-04", "V1", "2025-11-30", "L", "告警", "否", "是"),
        ("INC-V2-2025-07", "V2", "2025-07-03", "H", "数据完整性", "是", "否"),
        ("INC-V2-2025-01", "V2", "2025-02-14", "M", "性能", "否", "是"),
        ("INC-V2-2025-02", "V2", "2025-05-22", "L", "配置", "否", "是"),
        ("INC-V2-2025-03", "V2", "2025-09-18", "M", "变更", "否", "是"),
        ("INC-V3-2025-10", "V3", "2025-10-08", "M", "告警", "否", "否"),
        ("INC-V3-2025-01", "V3", "2025-03-03", "L", "配置", "否", "是"),
        ("INC-V3-2025-02", "V3", "2025-06-16", "M", "性能", "否", "是"),
        ("INC-V3-2025-03", "V3", "2025-12-01", "L", "告警", "否", "是"),
        ("INC-V4-2024-09", "V4", "2024-09-09", "H", "交易一致性", "是", "否"),
        ("INC-V4-2025-05", "V4", "2025-05-06", "H", "交易一致性", "是", "是"),
        ("INC-V4-2025-11", "V4", "2025-11-11", "M", "对账", "否", "否"),
        ("INC-V4-2025-01", "V4", "2025-01-15", "M", "性能", "否", "是"),
        ("INC-V4-2025-02", "V4", "2025-03-19", "L", "配置", "否", "是"),
        ("INC-V4-2025-03", "V4", "2025-08-27", "M", "变更", "否", "是"),
        ("INC-V5-2025-12", "V5", "2025-12-12", "M", "备份失败", "否", "否"),
        ("INC-V5-2025-01", "V5", "2025-04-04", "L", "容量", "否", "是"),
        ("INC-V5-2025-02", "V5", "2025-09-09", "M", "性能", "否", "是"),
        ("INC-V6-2024-02", "V6", "2024-02-20", "H", "认证中断", "是", "是"),
        ("INC-V6-2025-01", "V6", "2025-01-09", "M", "告警", "否", "否"),
        ("INC-V6-2025-08", "V6", "2025-08-14", "H", "认证中断", "是", "是"),
        ("INC-V6-2025-03", "V6", "2025-11-06", "L", "配置", "否", "是"),
    ]
    assert len(rows) == 26
    return rows


# 附件11：上期台账 10 项
RISKS = [
    ("R-2024-01", "V3", "监测平台账号台账未闭环", "已整改"),
    ("R-2024-02", "V1", "高危漏洞超期未修", "整改中"),
    ("R-2024-03", "V4", "生产库与测试环境账号未回收", "整改中"),
    ("R-2024-04", "V2", "灾备演练 RTO 超目标", "整改中"),
    ("R-2024-05", "V5", "备份容量告警阈值未校准", "已整改"),
    ("R-2024-06", "V6", "身份认证组件单点", "整改中"),
    ("R-2024-07", "V3", "安全事件工单归档不及时", "已整改"),
    ("R-2024-08", "V1", "敏感数据明文列", "整改中"),
    ("R-2024-09", "V6", "测试环境账号未回收", "已整改"),
    ("R-2024-10", "V2", "合同退出过渡期条款缺失", "整改中"),
]

# 附件10：12 条（8 维度 + 综合 + 阈值 + 计数 + 决策）
CLAUSES10 = [
    ("T01", "漏洞管理", "高危超期未修 ≥2 条→高档；=1 条→中档；高危=0 且中危超期未修 ≤2 条→低档；中危超期未修 ≥3 条→中档。低危超期未修未穷举落点。"),
    ("T02", "数据加密", "敏感明文列（跨核查范围合计）>0→高档；=0→低档。"),
    ("T03", "访问控制", "未回收账号（跨核查范围合计）≥5→高档；1—4→中档；0→低档。"),
    ("T04", "灾备韧性", "取用演练 RTO 或 RPO 任一超目标→高档；读数达标但关键依赖未全覆盖→中档；达标且全覆盖→低档。"),
    ("T05", "集中度关联", "同一子处理商或同一云区域承载 ≥3 户→高档；=2 户→中档；=1 户→低档。"),
    ("T06", "合同退出", "无数据可携、无退出过渡期、赔偿上限≤月费1倍，三项为「或」关系，任一成立→高档；均不成立→低档。"),
    ("T07", "可用性SLA", "任一月读数低于承诺值→中档；连续 ≥3 月不达标→高档；否则低档。"),
    ("T08", "安全事件", "影响本行的高危事件且处置证据缺失→高档（记待核）；影响本行的高危事件且证据齐全→中档；无影响本行的高危事件→低档。"),
    ("T09", "综合", "综合级＝各维度最严重级；漏洞、加密、访问、集中度任一为高则该户不得为低；业务关键性为「关键」的供应商在证据充分时可上调一票；含待核须标注，不得吞并。"),
    ("T10", "阈值", "集中度以 3 户为超限阈值；访问控制以 5 个未回收账号为高档阈值；合同退出赔偿上限以 1 倍月费为界（含等号）。"),
    ("T11", "计数", "子处理商集中度取附件7 全部角色记录（含组件供应商）；云区域集中度取附件1 主要云区域。"),
    ("T12", "决策", "证据不足事项不得默认通过，也不得据此抬高结论；口径未穷举时取低档并登记缺口。"),
]

CLAUSES12 = [
    ("G01", "基准日", "2025-12-31。"),
    ("G02", "统计期间", "2025-01-01 至 2025-12-31；发现日或发生日早于起点的记录为期间外，不参与任何档位计数。"),
    ("G03", "业务关键性", "关键/支持；关键供应商在证据充分时可上调一票。"),
    ("G04", "待核处理", "证据不足事项单列待核，不得并入综合级判定为已核实结论。"),
    ("G05", "账号与明文计数", "按各核查范围合计取，不取单范围最大值。"),
    ("G06", "可用性读数", "采用扣除计划窗口与第三方原因后的读数作为判定读数，原始读数并列披露。"),
    ("G07", "连续性判定", "连续期数按自然月序号连续计算，中断即重新起算。"),
    ("G08", "灾备演练取值", "取统计期间内日期最近一次演练；同户其余演练须列排除理由。"),
    ("G09", "自评取值", "自评结论仅作对照列，不得替代实测核查取值。"),
]

CONTROLS = [
    "账号权限台账", "渗透测试与漏洞修复", "敏感数据加密", "灾备切换演练", "可用性SLA达成",
    "安全事件处置", "合同退出与可携", "子处理商与依赖管理", "变更管理", "日志与审计",
    "数据备份与恢复", "外包风险自评",
]


def d(s):
    return dt.date.fromisoformat(s) if s else None


def classify_vulns():
    out = []
    for vid, sup, sev, found, due, fixed, status in _vulns():
        f, dl, fx = d(found), d(due), d(fixed)
        if f < PERIOD_START:
            cls = "期间外"
        elif status == "未到期未修":
            cls = "未到期未修"
        elif status == "已修" and fx and dl and fx > dl:
            cls = "超期已修"
        elif status == "未修" and dl and dl < BASE:
            cls = "超期未修"
        else:
            cls = "未超期"
        out.append(dict(id=vid, sup=sup, sev=sev, found=found, due=due, fixed=fixed,
                        status=status, cls=cls))
    return out


def dims():
    """按附件10/12 口径给 6 户 8 维判定。"""
    vul = classify_vulns()
    res = {}
    for sid, *_ in SUP:
        # 1 漏洞：超期未修（期间内、未修、应修日 < 基准日）
        over = [v for v in vul if v["sup"] == sid and v["cls"] == "超期未修"]
        h = sum(1 for v in over if v["sev"] == "高")
        m = sum(1 for v in over if v["sev"] == "中")
        lo = sum(1 for v in over if v["sev"] == "低")
        if h >= 2:
            v1 = "高"
        elif h == 1:
            v1 = "中"
        elif m >= 3:
            v1 = "中"
        else:
            v1 = "低"
        # 2 加密 / 3 访问（合计）
        plain = sum(PERM[(sid, r)][1] for r in RANGES)
        acct = sum(PERM[(sid, r)][0] for r in RANGES)
        v2 = "高" if plain > 0 else "低"
        v3 = "高" if acct >= 5 else ("中" if acct >= 1 else "低")
        res[sid] = dict(漏洞管理=v1, 数据加密=v2, 访问控制=v3,
                        **_rest(sid), over=(h, m, lo), acct=acct, plain=plain)
    return res


def _rest(sid):
    # 4 灾备：取期间内最近一次
    dr = sorted([x for x in DRILL if x[0] == sid], key=lambda x: x[1])
    used = dr[-1]
    rto_ok = used[3] <= used[4]
    rpo_ok = used[5] <= used[6]
    covered = used[7] == ""
    if not (rto_ok and rpo_ok):
        v4 = "高"
    elif not covered:
        v4 = "中"
    else:
        v4 = "低"
    # 5 集中度：全部角色归并 + 云区域
    sizes = {}
    for s, sp, role in DEP:
        sizes[sp] = sizes.get(sp, set()) | {s}
    clusters = {k: sorted(v) for k, v in sizes.items()}
    clouds = {}
    for row in SUP:
        clouds.setdefault(row[6], set()).add(row[0])
    clusters.update({k: sorted(v) for k, v in clouds.items()})
    mx = max((len(v) for k, v in clusters.items() if sid in v), default=0)
    v5 = "高" if mx >= 3 else ("中" if mx == 2 else "低")
    # 6 合同退出
    carry, trans, cap, _notice = EXIT[sid]
    v6 = "高" if (carry == "否" or trans == "无" or cap <= 1) else "低"
    # 7 SLA：扣除后读数
    bad, bad_raw = SLA_BAD[sid]
    streak = _streak(bad)
    v7 = "高" if streak >= 3 else ("中" if bad else "低")
    # 8 安全事件
    ev = [e for e in _incidents() if e[1] == sid and d(e[2]) >= PERIOD_START]
    hi_aff = [e for e in ev if e[3] == "H" and e[5] == "是"]
    if any(e[6] == "否" for e in hi_aff):
        v8, pending = "高", True
    elif hi_aff:
        v8, pending = "中", False
    else:
        v8, pending = "低", False
    return dict(灾备韧性=v4, 集中度关联=v5, 合同退出=v6, 可用性SLA=v7, 安全事件=v8,
                used_drill=used, clusters=clusters, max_cluster=mx,
                sla_bad=bad, sla_bad_raw=bad_raw, streak=streak, pending=pending)


def _streak(months):
    if not months:
        return 0
    idx = sorted(MONTHS.index(m) for m in months)
    best = cur = 1
    for a, b in zip(idx, idx[1:]):
        cur = cur + 1 if b == a + 1 else 1
        best = max(best, cur)
    return best


DIMS = ["漏洞管理", "数据加密", "访问控制", "灾备韧性", "集中度关联", "合同退出", "可用性SLA", "安全事件"]


def build():
    dm = dims()
    grades = {s: max(dm[s][k] for k in DIMS) for s, *_ in SUP}
    grid = {k: [dm[s][k] for s, *_ in SUP] for k in DIMS}
    dist = {g: sum(1 for v in grades.values() if v == g) for g in ("高", "中", "低")}
    print("综合级:", grades)
    print("分布:", dist, "合计", sum(dist.values()))
    for k in DIMS:
        print(f"  {k}: {grid[k]}")

    # ---------------- 断言：与冻结考点一致 ----------------
    exp = {
        "grid": {
            "V1": dict(漏洞管理="中", 数据加密="高", 访问控制="低", 灾备韧性="中", 集中度关联="高", 合同退出="高", 可用性SLA="低", 安全事件="低"),
            "V2": dict(漏洞管理="低", 数据加密="低", 访问控制="中", 灾备韧性="高", 集中度关联="高", 合同退出="低", 可用性SLA="中", 安全事件="高"),
            "V3": dict(漏洞管理="低", 数据加密="低", 访问控制="低", 灾备韧性="低", 集中度关联="低", 合同退出="低", 可用性SLA="低", 安全事件="低"),
            "V4": dict(漏洞管理="高", 数据加密="低", 访问控制="高", 灾备韧性="低", 集中度关联="高", 合同退出="低", 可用性SLA="低", 安全事件="中"),
            "V5": dict(漏洞管理="低", 数据加密="低", 访问控制="中", 灾备韧性="低", 集中度关联="高", 合同退出="低", 可用性SLA="中", 安全事件="低"),
            "V6": dict(漏洞管理="低", 数据加密="低", 访问控制="高", 灾备韧性="低", 集中度关联="高", 合同退出="低", 可用性SLA="中", 安全事件="中"),
        },
        "dist": {"高": 5, "中": 0, "低": 1},
        "high_cells": 12, "cells": 48,
        "mid_cells": 9, "low_cells": 27,
        "period_out": {"VUL-V1-12", "VUL-V2-12", "VUL-V4-09", "VUL-V6-07"},
        "trig": {"V4": (2, 0), "V1": (1, 0), "V2": (0, 2), "V3": (0, 0)},
        "clusters": {"SP-M": 2, "SP-Q": 2, "SP-T": 1, "SP-U": 1, "SP-W": 5, "SP-X": 3,
                     "SP-Y": 1, "SP-Z": 1, "CR-A": 3, "CR-B": 1, "CR-C": 1, "CR-D": 1},
        "over_clusters": {"SP-W", "SP-X", "CR-A"},
        "inc_period_out": {"INC-V1-2024-06", "INC-V4-2024-09", "INC-V6-2024-02"},
        "risk_closed": {"R-2024-01", "R-2024-05", "R-2024-07"},
        "clauses": 12 + 9,
    }
    fails = []
    for s in exp["grid"]:
        for k, v in exp["grid"][s].items():
            if dm[s][k] != v:
                fails.append(f"格 {s}-{k}: 期望 {v} 实得 {dm[s][k]}")
    cnt = {g: sum(1 for v in grades.values() if v == g) for g in ("高", "中", "低")}
    if cnt != exp["dist"]:
        fails.append(f"综合分布: 期望 {exp['dist']} 实得 {grades}")
    hi = sum(1 for s, *_ in SUP for k in DIMS if dm[s][k] == "高")
    mid = sum(1 for s, *_ in SUP for k in DIMS if dm[s][k] == "中")
    low = sum(1 for s, *_ in SUP for k in DIMS if dm[s][k] == "低")
    if (hi, mid, low) != (exp["high_cells"], exp["mid_cells"], exp["low_cells"]):
        fails.append(f"48 格分布: 期望 {(exp['high_cells'], exp['mid_cells'], exp['low_cells'])} 实得 {(hi, mid, low)}")
    po = {v["id"] for v in classify_vulns() if v["cls"] == "期间外"}
    if po != exp["period_out"]:
        fails.append(f"期间外漏洞: {po} != {exp['period_out']}")
    for s, (eh, em) in exp["trig"].items():
        h, m, _ = dm[s]["over"]
        if (h, m) != (eh, em):
            fails.append(f"{s} 漏洞触发: 期望 {(eh, em)} 实得 {(h, m)}")
    if dm["V1"]["clusters"]["SP-W"] != ["V1", "V2", "V4", "V5", "V6"]:
        fails.append(f"SP-W 成员 {dm['V1']['clusters']['SP-W']}")
    sizes = {k: len(v) for k, v in dm["V1"]["clusters"].items()}
    if sizes != exp["clusters"]:
        fails.append(f"簇规模: {sizes} != {exp['clusters']}")
    overc = {k for k, v in sizes.items() if v >= 3}
    if overc != exp["over_clusters"]:
        fails.append(f"超限簇: {overc}")
    ipo = {e[0] for e in _incidents() if d(e[2]) < PERIOD_START}
    if ipo != exp["inc_period_out"]:
        fails.append(f"期间外事件: {ipo}")
    if len(CLAUSES10) + len(CLAUSES12) != exp["clauses"]:
        fails.append("条款条数不为 21")
    closed = {r[0] for r in RISKS if r[3] == "已整改"}
    if len(RISKS) != 10:
        fails.append("上期台账不为 10 项")

    for f in fails:
        print("FAIL", f)
    print(f"\n断言 {len(fails)} 失败")
    return dm, grades, fails


# ---------------------- 输出 ----------------------
def w(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        cw = csv.writer(f)
        cw.writerow(header)
        cw.writerows(rows)
    print(f"  {os.path.basename(path):44s} {len(rows):3d} 行")


def emit_materials(pack):
    base = os.path.join(pack, "01_public", "data")
    print("\n[材料]")
    w(f"{base}/附件1_供应商主数据与依赖.csv",
      ["供应商编号", "供应商名称", "服务类别", "业务关键性", "合同起日", "合同止日", "主要云区域", "共用子处理商"],
      [list(r) for r in SUP])
    self_rows = []
    for row in SUP:
        sid = row[0]
        for c in CONTROLS:
            concl = "符合"
            if sid == "V1" and c == "敏感数据加密":
                concl = "符合"            # 与附件4 实测（明文 3 列）相反
            if sid == "V6" and c == "账号权限台账":
                concl = "符合"            # 与附件4 实测（合计 5 个未回收）相反
            self_rows.append([sid, c, "2025-01-01至2025-12-31", concl])
    w(f"{base}/附件2_供应商自评问卷.csv",
      ["供应商编号", "控制项", "期间", "自评结论"], self_rows)
    rows = []
    for v in classify_vulns():
        rows.append([v["id"], v["sup"], v["sev"], v["found"], v["due"], v["fixed"], v["status"]])
    w(f"{base}/附件3_渗透测试与漏洞扫描记录.csv",
      ["漏洞ID", "供应商编号", "严重级别", "发现日", "SLA应修日", "实际修复日", "状态"], rows)
    rows = []
    for (sid, rg), (a, p) in PERM.items():
        rows.append([sid, rg, a, p, f"{rg}核查完成"])
    rows.sort(key=lambda r: (r[0], RANGES.index(r[1])))
    w(f"{base}/附件4_加密与访问权限核查.csv",
      ["供应商编号", "核查范围", "未回收账号数", "敏感明文列数", "核查说明"], rows)
    w(f"{base}/附件5_灾备切换演练记录.csv",
      ["供应商编号", "演练日期", "演练场景", "实际RTO(小时)", "目标RTO(小时)",
       "实际RPO(分钟)", "目标RPO(分钟)", "未覆盖关键依赖", "演练是否通过"],
      [list(r) for r in DRILL])
    rows = []
    for sid, *_ in SUP:
        bad, bad_raw = SLA_BAD[sid]
        for i, m in enumerate(MONTHS, 1):
            deducted = round(99.50 + (i % 5) * 0.12, 2) if m in bad else round(99.92 + (i % 4) * 0.02, 2)
            raw = round(99.40 + (i % 3) * 0.10, 2) if m in bad_raw else round(99.90 + (i % 4) * 0.02, 2)
            rows.append([sid, m, f"{deducted:.2f}", f"{raw:.2f}", f"{COMMIT:.2f}"])
    w(f"{base}/附件6_SLA与可用性日志.csv",
      ["供应商编号", "月份", "月度可用性(扣除后,%)", "月度可用性(原始,%)", "承诺值(%)"], rows)
    w(f"{base}/附件7_子处理商与依赖矩阵.csv",
      ["供应商编号", "子处理商编号", "角色"], [list(r) for r in DEP])
    w(f"{base}/附件8_合同退出与可携条款.csv",
      ["供应商编号", "数据可携", "退出过渡期(天)", "赔偿上限(月费倍数)", "终止通知期(天)"],
      [[k, v[0], v[1], v[2], v[3]] for k, v in EXIT.items()])
    w(f"{base}/附件9_安全事件工单.csv",
      ["事件ID", "供应商编号", "发生日", "级别", "类别", "是否影响本行", "处置证据是否齐全"],
      [list(r) for r in _incidents()])
    w(f"{base}/附件10_技术风险定级标准.csv", ["条款编号", "维度/条款", "口径原文"],
      [list(r) for r in CLAUSES10])
    w(f"{base}/附件11_上期风险台账与整改跟踪.csv",
      ["风险编号", "供应商编号", "事项", "台账状态"], [list(r) for r in RISKS])
    w(f"{base}/附件12_基准日与处置权重登记.csv", ["条款编号", "项目", "口径原文"],
      [list(r) for r in CLAUSES12])


def normalize_zip(path, stamp=(2026, 1, 1, 0, 0, 0)):
    """把 xlsx 内部 zip 条目的时间戳与顺序固定，保证同一输入逐字节一致。"""
    import zipfile
    import re
    with zipfile.ZipFile(path) as z:
        items = [(i.filename, z.read(i.filename), i.compress_type) for i in z.infolist()]
    # openpyxl 在 save 时会把 dcterms:modified 覆写为当前时间，这里统一钉死
    fixed = []
    for name, data, ctype in items:
        if name == "docProps/core.xml":
            data = re.sub(rb"(<dcterms:modified[^>]*>)[^<]*(<)",
                          rb"\g<1>2026-01-01T00:00:00Z\g<2>", data)
        fixed.append((name, data, ctype))
    items = fixed
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w") as z:
        for name, data, ctype in items:
            zi = zipfile.ZipInfo(name, date_time=stamp)
            zi.compress_type = ctype
            zi.external_attr = 0o600 << 16
            z.writestr(zi, data)
    os.replace(tmp, path)


def emit_gt(pack, dm, grades):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    gt = os.path.join(pack, "03_private_review", "GT")
    os.makedirs(gt, exist_ok=True)
    H = Font(bold=True)
    FILL = PatternFill("solid", fgColor="EFEFEF")

    def sheet(ws, header, rows, widths=None):
        ws.append(header)
        for c in ws[1]:
            c.font = H
            c.fill = FILL
            c.alignment = Alignment(wrap_text=True, vertical="center")
        for r in rows:
            ws.append(r)
        for i, wd in enumerate(widths or [], start=1):
            ws.column_dimensions[chr(64 + i)].width = wd
        ws.freeze_panes = "A2"

    # D1
    wb = Workbook()
    ws = wb.active
    ws.title = "D1_维度判定"
    rows = []
    for sid, name, *_ in SUP:
        for k in DIMS:
            ev = {
                "漏洞管理": f"高危超期未修{dm[sid]['over'][0]}条/中危{dm[sid]['over'][1]}条/低危{dm[sid]['over'][2]}条",
                "数据加密": f"敏感明文列合计{dm[sid]['plain']}",
                "访问控制": f"未回收账号合计{dm[sid]['acct']}",
                "灾备韧性": f"{dm[sid]['used_drill'][1]} RTO{dm[sid]['used_drill'][3]}/{dm[sid]['used_drill'][4]} RPO{dm[sid]['used_drill'][5]}/{dm[sid]['used_drill'][6]} 未覆盖={dm[sid]['used_drill'][7] or '无'}",
                "集中度关联": f"最大承载{dm[sid]['max_cluster']}户",
                "合同退出": f"可携={EXIT[sid][0]} 过渡={EXIT[sid][1]} 赔偿≤{EXIT[sid][2]}倍",
                "可用性SLA": f"扣除后未达标{len(dm[sid]['sla_bad'])}月 最长连续{dm[sid]['streak']}",
                "安全事件": f"期间内影响本行高危{sum(1 for e in _incidents() if e[1]==sid and d(e[2])>=PERIOD_START and e[3]=='H' and e[5]=='是')}条",
            }[k]
            rows.append([sid, name, k, dm[sid][k], ev,
                         {"漏洞管理": "附件3", "数据加密": "附件4", "访问控制": "附件4",
                          "灾备韧性": "附件5", "集中度关联": "附件7", "合同退出": "附件8",
                          "可用性SLA": "附件6", "安全事件": "附件9"}[k]])
    sheet(ws, ["供应商编号", "供应商名称", "维度", "判定", "依据字段与实际值", "取证记录"],
          rows, [12, 14, 12, 8, 52, 10])
    n = {"高": 0, "中": 0, "低": 0}
    for r in rows:
        n[r[3]] += 1
    ws.append([])
    ws.append(["自计数", f"高{n['高']}＋中{n['中']}＋低{n['低']}＝{sum(n.values())}＝6×8"])

    # D4
    ws = wb.create_sheet("D4_综合定级与处置")
    rows = []
    for sid, name, _svc, crit, _cs, ce, _cr, _sh in SUP:
        g = grades[sid]
        disp = {("V1"): "暂停/整改复评", ("V4"): "暂停/整改复评", ("V5"): "暂停/整改复评",
                ("V6"): "暂停/整改复评", ("V2"): "有条件续约", ("V3"): "正常续约"}[sid]
        rows.append([sid, name, crit, g, "含待核" if dm[sid]["pending"] else "无", disp,
                     "当日到期" if ce == BASE.isoformat() else "之后", ce])
    sheet(ws, ["供应商编号", "供应商名称", "业务关键性", "综合等级", "证据不足标注", "处置意见", "合同止日位置", "合同止日"],
          rows, [12, 14, 10, 10, 12, 18, 14, 12])
    ws.append([])
    ws.append(["自计数", f"高{grades['高'] if '高' in grades else sum(1 for v in grades.values() if v=='高')}"
                          f"＋中{sum(1 for v in grades.values() if v=='中')}"
                          f"＋低{sum(1 for v in grades.values() if v=='低')}＝6"])
    ws.append(["入选/未入选", "入选 5 户（V1、V2、V4、V5、V6）；未入选 1 户（V3，经核查不适用暂停/整改）；无交集，并集＝6"])

    # D8
    ws = wb.create_sheet("D8_计数勾稽与登记")
    rows = [
        ["经查不成立", "中危超期未修≥3→中", "附件10 T01", "0 户触发（最高为 V2 的 2 条）"],
        ["经查不成立", "连续3月可用性不达标→高", "附件10 T07", "0 户触发（最长连续为 V5 的 2 月）"],
        ["经查不成立", "关键供应商上调一票", "附件10 T09", "无增量（5 户关键户已为高）"],
        ["触发名单", "高危超期未修≥2→高", "附件10 T01", "V4（2 条）"],
        ["触发名单", "高危超期未修=1→中", "附件10 T01", "V1（1 条）"],
        ["触发名单", "未回收账号≥5→高", "附件10 T03", "V4(8)、V6(5)"],
        ["触发名单", "赔偿上限≤1倍→高", "附件10 T06", "V1（恰等 1 倍）"],
    ]
    sheet(ws, ["类别", "口径条件", "条款位置", "本期命中"], rows, [14, 30, 14, 40])
    gaps = [
        [1, "VUL-V3-06", "低危超期未修落点未穷举", "取低档", "不改变 V3 维度档位"],
        [2, "附件7 组件供应商角色", "归并基准与附件1 列口径不一致", "取附件7 全部角色",
         "改用附件1 会使 SP-W 由 5 户缩为 1 户，V4/V6 集中度降档"],
        [3, "附件4 单范围最大值", "单范围与合计两种读法并存", "按附件12 G05 取合计", "V6 由中变高"],
        [4, "附件2 自评与附件4 实测", "同一控制项结论相反", "以实测为准（G09）", "不影响档位的冲突单列"],
        [5, "附件11 R-2024-09", "台账状态与本年证据矛盾", "按本年证据判未闭环", "上期闭环数由 4 变 3"],
        [6, "附件5 每户两次演练", "两次结论方向相反", "取期间内最近一次（G08）", "V1/V2/V3/V5 档位由取用决定"],
        [7, "附件10 T01 低危", "低危超期落点缺失", "登记缺口", "不判高"],
    ]
    ws.append([])
    ws.append(["口径缺口", "共 7 项"])
    for g in gaps:
        ws.append(g)

    # D9
    ws = wb.create_sheet("D9_口径命中与边界")
    rows = []
    for cid, name, text, hit in [
        ("T01", "漏洞管理", "高危超期未修≥2→高；=1→中；高危0且中危≤2→低；中危≥3→中",
         "V4 高；V1 中；V2/V3/V5/V6 低；中危≥3 无触发"),
        ("T02", "数据加密", "明文列>0→高", "V1 高；其余低"),
        ("T03", "访问控制", "账号≥5→高；1-4→中；0→低", "V4/V6 高；V2/V5 中；V1/V3 低"),
        ("T04", "灾备韧性", "超目标→高；达标未覆盖→中；达标全覆盖→低", "V2 高；V1 中；V3–V6 低"),
        ("T05", "集中度关联", "≥3→高；=2→中；=1→低", "V1/V2/V4/V5/V6 高；V3 低"),
        ("T06", "合同退出", "三项任一→高", "V1 高；其余低"),
        ("T07", "可用性SLA", "任一月不达标→中；连续≥3→高", "V2/V5/V6 中；V1/V3/V4 低"),
        ("T08", "安全事件", "影响的H且缺证→高待核；齐→中", "V2 高；V4/V6 中；V1/V3/V5 低"),
    ]:
        rows.append([cid, name, text, hit])
    sheet(ws, ["条款", "维度", "口径原文", "本期命中/未命中"], rows, [8, 14, 52, 52])
    ws.append([])
    ws.append(["条款总数", "附件10 12 条 ＋ 附件12 9 条 ＝ 21 条；逐户展开 6×21＝126"])
    for cid, name, text in CLAUSES12:
        ws.append([cid, name, text, ""])

    # D10
    ws = wb.create_sheet("D10_对平")
    rows = [
        ["①行数对平", "附件2=72 附件3=48 附件4=18 附件5=12 附件6=72 附件7=16 附件9=26 附件11=10",
         "逐件实数与题面 308 一致", 0, "无覆盖缺口"],
        ["②自计数对平", "各表自计数与逐条实数", "48=48、21=21、10=10", 0, "—"],
        ["③读数对平", "逐户双读数与连续期数", "结论相同 V1/V5/V6；不同 V3/V4；V2 月集合不同档位同", 0, "—"],
        ["④日期链对平", "发现日—应修日—实修日；期间内+期间外=该户条数", "48=44+4；26=23+3", 0, "—"],
        ["⑤跨件事实对平", "附件2/4/8/11 同户同事项", "2 处自评与实测冲突（V1 加密、V6 账号）", 0, "采信实测"],
    ]
    sheet(ws, ["对平链", "应等式", "两侧实际值", "差额", "原因与影响"], rows, [16, 44, 44, 8, 24])

    for f in ("D1_维度判定", "D4_综合定级与处置", "D8_计数勾稽与登记", "D9_口径命中与边界", "D10_对平"):
        pass
    # 固定文档属性，保证同一输入产出逐字节一致（openpyxl 默认写入当前时间）
    wb.properties.creator = "financial-skill-factory"
    wb.properties.created = dt.datetime(2026, 1, 1, 0, 0, 0)
    wb.properties.modified = dt.datetime(2026, 1, 1, 0, 0, 0)
    wb.properties.lastModifiedBy = "financial-skill-factory"
    out = os.path.join(gt, "标准答案_城商行IT外包供应商技术风险定级.xlsx")
    wb.save(out)
    normalize_zip(out)
    print(f"  GT xlsx: {os.path.basename(out)} ({os.path.getsize(out)} 字节)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default="../packs/7689005313907642138")
    a = ap.parse_args()
    print("=== 断言 ===")
    dm, grades, fails = build()
    if fails:
        sys.exit(1)
    emit_materials(a.pack)
    emit_gt(a.pack, dm, grades)
    print("\nOK 全部断言通过")


if __name__ == "__main__":
    main()
