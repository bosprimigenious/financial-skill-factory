# READINESS

题包：`7689005313907642138` 城商行IT外包供应商技术风险定级与处置意见底稿
状态：**READY_FOR_SUBMISSION**（12/12 检查通过）

## 产物

| 产物 | 路径 | 状态 |
|---|---|---|
| 选题依据（119 → 1） | `packs/SELECTION-FROM-119.md` | 完成 |
| 题面（含合成数据说明） | `01_public/task_prompt.md` | 完成 |
| 被试材料 12 件 CSV（307 行） | `01_public/data/` | 完成，脚本可复现 |
| 材料契约与验收 | `02_platform_fields/MATERIALS-CONTRACT.md` | 完成 |
| 隐藏难点 14 项 | `02_platform_fields/hidden_difficulties.md` | 完成 |
| 冻结考点 12 条＝100 分 | `02_platform_fields/expert_rubric.md` | 完成（含 1 条修订留痕） |
| 作答思路 50 步 | `02_platform_fields/ideal_steps.md` | 完成 |
| 标准答案（文字＋xlsx 五表） | `03_private_review/GT/` | 完成 |
| 逐条判分（豆包卷 46/100） | `04_evidence/score_12.md` | 完成 |
| 自测与门槛核算 | `04_evidence/self_test_record.md` | 完成 |
| 12 项检查 | `05_submission/CHECKLIST-12.md` | 12/12 PASS |
| 机器校验 | `tools/verify_pack.py` | 24/24 PASS |

## 门槛

| 条件 | 实测 | 判定 |
|---|---|---|
| 得分 ≤50 | 46 | PASS |
| 步数 ≥50 或 时间 >2400 秒 | 2916 秒 | PASS |

**LOCAL_ACCEPTED（门槛侧）**，不等于平台通过。二轮质检以「22 步 < 25 步」关闭，与现行书面口径不一致；22 步属质检侧统计，作者侧不可核验。

## 复现

```bash
python3 cases/ccb-vendor-tpr-2026/build_case.py --pack packs/7689005313907642138
python3 tools/verify_pack.py packs/7689005313907642138
```

改任一附件数据后重跑构建器：断言会逐格重算，任一格与冻结考点不符即非零退出。
