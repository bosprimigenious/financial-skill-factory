#!/usr/bin/env python3
"""题包机器校验：材料、权重、条数、隔离、勾稽、考点覆盖、GT 附件。

用法：python3 tools/verify_pack.py packs/7689005313907642138
退出码：0 全通过；1 有 FAIL；2 缺关键文件。
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

PACK = sys.argv[1] if len(sys.argv) > 1 else "packs/7689005313907642138"
checks: list[tuple[str, bool, str]] = []


def chk(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, ok, detail))


def read(p: str) -> str:
    with open(os.path.join(PACK, p), encoding="utf-8") as f:
        return f.read()


def rows(p: str) -> list[list[str]]:
    with open(os.path.join(PACK, p), encoding="utf-8", newline="") as f:
        return list(csv.reader(f))[1:]


NEED = [
    "00_meta.json", "01_public/task_prompt.md",
    "02_platform_fields/expert_rubric.md", "02_platform_fields/hidden_difficulties.md",
    "02_platform_fields/ideal_steps.md", "02_platform_fields/MATERIALS-CONTRACT.md",
    "03_private_review/GT/golden_response.md", "04_evidence/score_12.md",
    "04_evidence/self_test_record.md", "05_submission/CHECKLIST-12.md",
    "05_submission/READINESS.md",
]
missing = [p for p in NEED if not os.path.exists(os.path.join(PACK, p))]
chk("文件齐备", not missing, f"缺 {missing}")
if missing:
    print("FAIL 文件齐备:", missing)
    sys.exit(2)

meta = json.loads(read("00_meta.json"))
rub = read("02_platform_fields/expert_rubric.md")
prompt = read("01_public/task_prompt.md")
hd = read("02_platform_fields/hidden_difficulties.md")
sc = read("04_evidence/score_12.md")
gt = read("03_private_review/GT/golden_response.md")
cl = read("05_submission/CHECKLIST-12.md")

# ---- 1 材料：12 件、行数、必备字段 ----
MAT = {
    "附件1_供应商主数据与依赖.csv": (6, ["供应商编号", "合同止日", "主要云区域", "共用子处理商"]),
    "附件2_供应商自评问卷.csv": (72, ["供应商编号", "控制项", "期间", "自评结论"]),
    "附件3_渗透测试与漏洞扫描记录.csv": (48, ["漏洞ID", "供应商编号", "严重级别", "发现日", "SLA应修日", "实际修复日", "状态"]),
    "附件4_加密与访问权限核查.csv": (18, ["供应商编号", "核查范围", "未回收账号数", "敏感明文列数"]),
    "附件5_灾备切换演练记录.csv": (12, ["供应商编号", "演练日期", "实际RTO(小时)", "目标RTO(小时)", "未覆盖关键依赖"]),
    "附件6_SLA与可用性日志.csv": (72, ["供应商编号", "月份", "月度可用性(扣除后,%)", "月度可用性(原始,%)", "承诺值(%)"]),
    "附件7_子处理商与依赖矩阵.csv": (16, ["供应商编号", "子处理商编号", "角色"]),
    "附件8_合同退出与可携条款.csv": (6, ["供应商编号", "数据可携", "退出过渡期(天)", "赔偿上限(月费倍数)"]),
    "附件9_安全事件工单.csv": (26, ["事件ID", "供应商编号", "发生日", "级别", "是否影响本行", "处置证据是否齐全"]),
    "附件10_技术风险定级标准.csv": (12, ["条款编号", "维度/条款", "口径原文"]),
    "附件11_上期风险台账与整改跟踪.csv": (10, ["风险编号", "供应商编号", "事项", "台账状态"]),
    "附件12_基准日与处置权重登记.csv": (9, ["条款编号", "项目", "口径原文"]),
}
total = 0
for name, (n, cols) in MAT.items():
    p = f"01_public/data/{name}"
    if not os.path.exists(os.path.join(PACK, p)):
        chk(f"材料存在 {name}", False, "缺文件")
        continue
    body = rows(p)
    total += len(body)
    head = next(csv.reader(open(os.path.join(PACK, p), encoding="utf-8")))
    ok = len(body) == n and all(c in head for c in cols)
    chk(f"材料 {name}", ok, f"行 {len(body)}/{n} 字段缺 {[c for c in cols if c not in head]}")
chk("材料总行数=307", total == 307, f"实得 {total}")

# 期间外与边界记录必须在册
v3 = [r for r in rows("01_public/data/附件3_渗透测试与漏洞扫描记录.csv")]
ids3 = {r[0] for r in v3}
chk("期间外漏洞 4 条在册", {"VUL-V1-12", "VUL-V2-12", "VUL-V4-09", "VUL-V6-07"} <= ids3, "")
chk("低危超期缺口记录在册", "VUL-V3-06" in ids3, "")
ids9 = {r[0] for r in rows("01_public/data/附件9_安全事件工单.csv")}
chk("期间外事件 3 条在册", {"INC-V1-2024-06", "INC-V4-2024-09", "INC-V6-2024-02"} <= ids9, "")
chk("V2 待核事件在册", "INC-V2-2025-07" in ids9, "")
dep = rows("01_public/data/附件7_子处理商与依赖矩阵.csv")
spw = {r[0] for r in dep if r[1] == "SP-W"}
chk("SP-W 5 户（全部角色口径）", spw == {"V1", "V2", "V4", "V5", "V6"}, f"{spw}")
sup1 = rows("01_public/data/附件1_供应商主数据与依赖.csv")
spw_col = {r[0] for r in sup1 if "SP-W" in r[7]}
chk("附件1 列口径 SP-W 仅 1 户（陷阱成立）", len(spw_col) == 1, f"{spw_col}")

# ---- 2 考点 ----
items = re.findall(r"【第 (\d+) 条｜(\d+) 分】", rub)
ws = [int(w) for _, w in items]
chk("考点条数=12", len(items) == 12, f"{len(items)}")
chk("权重合计=100", sum(ws) == 100, f"{sum(ws)}")
chk("权重与 meta 一致", ws == meta["weights"], f"{ws}")

# ---- 3 题面 ----
chk("题面含 D1–D10", all(f"D{i}" in prompt for i in range(1, 11)), "")
chk("题面含合成数据说明", "合成数据" in prompt, "")
chk("题面硬性要求≥12", len(re.findall(r"^(\d+)\. ", prompt, re.M)) >= 12, "")

# ---- 4 难点 ----
hrows = re.findall(r"^\| (\d+) \| ", hd, re.M)
chk("隐藏难点 8–15", 8 <= len(hrows) <= 15, f"{len(hrows)}")

# ---- 5 隔离 ----
leak = [t for t in ("核心得分点", "达标判据", "隐藏难点", "标准答案", "golden") if t in prompt]
chk("01_public 无答案泄露", not leak, f"命中 {leak}")
pub = sorted(
    os.path.join(dp, f).replace(PACK + os.sep, "")
    for dp, _, fs in os.walk(os.path.join(PACK, "01_public")) for f in fs
)
allowed = {"01_public/task_prompt.md", "01_public/attachment_manifest.tsv"} | {
    f"01_public/data/{n}" for n in MAT}
chk("01_public 白名单", set(pub) <= allowed, f"越界 {sorted(set(pub) - allowed)[:3]}")

# ---- 6 GT 附件 ----
gtx = os.path.join(PACK, "03_private_review/GT/标准答案_城商行IT外包供应商技术风险定级.xlsx")
chk("GT xlsx 存在", os.path.exists(gtx), gtx)
if os.path.exists(gtx):
    from openpyxl import load_workbook
    wb = load_workbook(gtx, read_only=True)
    chk("GT 五表齐", {"D1_维度判定", "D4_综合定级与处置", "D8_计数勾稽与登记",
                      "D9_口径命中与边界", "D10_对平"} <= set(wb.sheetnames), str(wb.sheetnames))
    d1 = [r for r in wb["D1_维度判定"].iter_rows(min_row=2, values_only=True) if r[0]]
    chk("GT D1 48 格", len([r for r in d1 if r[2]]) == 48, f"{len(d1)}")

# ---- 7 判分勾稽 ----
w = {int(a): int(b) for a, b in items}
fail_items = [2, 3, 6, 9, 11, 12]
chk("失败六条=54", sum(w[i] for i in fail_items) == 54, f"{sum(w[i] for i in fail_items)}")
chk("通过六条=46", 100 - sum(w[i] for i in fail_items) == 46, "")
chk("score_12 合计=46", "46" in sc, "")

# ---- 8 答案键 ----
for tok, label in [("高 12 ＋ 中 9 ＋ 低 27", "48 格分布"),
                   ("高 5（V1、V2、V4、V5、V6）", "综合分布"),
                   ("计入 44 ＋ 期间外 4 ＝ 48", "漏洞勾稽"),
                   ("期间内 23 ＋ 期间外 3 ＝ 26", "事件勾稽"),
                   ("21 条", "条款勾稽"), ("7 项", "缺口项数"),
                   ("SP-W＝V1,V2,V4,V5,V6（5）", "集中度簇")]:
    chk(f"GT 含 {label}", tok in gt, tok)

# ---- 9 门槛与检查 ----
m = meta["measured"]
chk("门槛分数 46≤50", m["score_strict"] <= 50, "")
chk("门槛时间 2916>2400", m["platform_minutes"] * 60 > 2400, "")
chk("meta 状态就绪", meta["status"] == "READY_FOR_SUBMISSION", meta["status"])
crows = [int(r) for r in re.findall(r"^\| (\d+) \| ", cl, re.M) if int(r) <= 12]
chk("12 项检查齐", len(crows) == 12, f"{len(crows)}")
chk("结论 READY", "READY" in cl and "NOT READY" not in cl.split("结论")[1][:20], "")

print(f"PACK {PACK}")
for name, ok, detail in checks:
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
bad = [c for c in checks if not c[1]]
print(f"\n{len(checks) - len(bad)}/{len(checks)} PASS")
sys.exit(0 if not bad else 1)
